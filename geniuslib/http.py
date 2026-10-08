# GeniusLib - Clash of Clans API wrapper
# Based on coc.py (MIT License, copyright (c) 2019-2020 mathsman5133)
# (c) 2026 AkumaHalls / ClashGenius

import asyncio
import logging
import re
from base64 import b64decode as base64_b64decode
from collections import deque
from datetime import datetime, timezone
from itertools import cycle
from json import loads as json_loads
from time import monotonic, perf_counter
from typing import Optional
from urllib.parse import urlencode, urljoin, urlparse

import aiohttp
import orjson

from .errors import (
    ClashOfClansException,
    Forbidden,
    GatewayError,
    HTTPException,
    InvalidArgument,
    InvalidCredentials,
    Maintenance,
    NotFound,
    RateLimitError,
    RequestAborted,
)
from .middleware import Middleware
from .middleware import Request as MiddlewareRequest
from .middleware import Response as MiddlewareResponse
from .utils import FIFO, HTTPStats

LOG = logging.getLogger(__name__)
KEY_MINIMUM, KEY_MAXIMUM = 1, 10
LOGIN_TIMEOUT_SECONDS = 15
stats_url_matcher = re.compile(r"%23[\da-zA-Z]+|\d{8,}|global")

# Hosts that ``get_data_from_url`` is allowed to fetch. Payload-supplied URLs are
# attacker-controllable, so we only follow https URLs on Supercell/Clash domains.
ALLOWED_ASSET_HOSTS = frozenset({"clashofclans.com", "supercell.com"})
ALLOWED_ASSET_HOST_SUFFIXES = (".clashofclans.com", ".supercell.com")

# Cap on how long a single rate-limit backoff may pause the requester. The API
# communicates ``Retry-After`` in integer seconds; a server-controlled value is
# unbounded, and the sleep happens while holding the request permits, so an
# oversized header would stall every subsequent call on the client.
MAX_RATE_LIMIT_BACKOFF = 60

# Upper bound for redirect hops followed while downloading an asset; each hop is
# re-validated against the asset-host allowlist before it is followed.
MAX_ASSET_REDIRECTS = 5


def _is_allowed_asset_host(host: str) -> bool:
    """Return whether ``host`` is ``clashofclans.com``/``supercell.com`` or a subdomain of either."""
    host = (host or "").lower().rstrip(".")
    return host in ALLOWED_ASSET_HOSTS or host.endswith(ALLOWED_ASSET_HOST_SUFFIXES)


def _parse_retry_after(value: Optional[str]) -> Optional[int]:
    """Parse a ``Retry-After`` header.

    Only integer-seconds values are honoured; HTTP-date forms are ignored (the
    caller then falls back to its exponential-ish backoff).
    """
    if value is None:
        return None
    value = str(value).strip()
    if value.isdigit():
        return int(value)
    return None


async def json_or_text(response: aiohttp.ClientResponse):
    """Parses an aiohttp response into a the string or json response."""
    try:
        ret = await response.json(loads=orjson.loads)
    except (aiohttp.ContentTypeError, ValueError, orjson.JSONDecodeError):
        # Wrong content type (e.g. text/html) *or* a JSON body that is malformed:
        # fall back to the raw text instead of letting the decode error escape
        # the request retry loop.
        ret = await response.text(encoding="utf-8")

    return ret


class BasicThrottler:
    """Basic throttler that sleeps for `sleep_time` seconds between each request."""

    __slots__ = (
        "sleep_time",
        "last_run",
        "lock",
    )

    def __init__(self, sleep_time):
        self.sleep_time = sleep_time
        self.last_run = None
        self.lock = asyncio.Lock()
        LOG.debug("BasicThrottler initialized with sleeptime %s", self.sleep_time)

    async def __aenter__(self):
        async with self.lock:
            last_run = self.last_run
            if last_run:
                difference = monotonic() - last_run
                need_to_sleep = self.sleep_time - difference
                if need_to_sleep > 0:
                    LOG.debug("Request throttled. Sleeping for %s", need_to_sleep)
                    await asyncio.sleep(need_to_sleep)

            self.last_run = monotonic()
            return self

    async def __aexit__(self, exception_type, exception, traceback):
        pass


class BatchThrottler:
    """Simple throttler that allows `rate_limit` requests (per second) before sleeping until the next second."""

    __slots__ = (
        "rate_limit",
        "per",
        "retry_interval",
        "_task_logs",
    )

    def __init__(self, rate_limit, per=1.0, retry_interval=0.001):
        self.rate_limit = rate_limit
        self.per = per
        self.retry_interval = retry_interval

        self._task_logs = deque()
        LOG.debug("BatchThrottler initialized with rate_limit %s, per %s, retry_interval %s", self.rate_limit, self.per,
                  self. retry_interval)

    async def __aenter__(self):
        while True:
            now = monotonic()

            # Pop items(which are start times) that are no longer in the
            # time window
            while self._task_logs:
                if now - self._task_logs[0] > self.per:
                    self._task_logs.popleft()
                else:
                    break

            # Exit the infinite loop when new task can be processed
            if len(self._task_logs) < self.rate_limit:
                break

            retry_interval = self.retry_interval
            LOG.debug("Request throttled. Sleeping for %s seconds.", retry_interval)
            await asyncio.sleep(retry_interval)

        # Push new task's start time
        self._task_logs.append(monotonic())

        return self

    async def __aexit__(self, exception_type, exception, traceback):
        pass


class Route:
    """Helper class to create endpoint URLs."""

    # ``realtime`` comes from ``Client._defaults`` and is a client-level flag only:
    # war endpoints append ``?realtime=true`` to the path themselves. It must never
    # be serialized into the query string, or it would pollute the cache key.
    ignored_kwargs = ['lookup_cache', 'update_cache', 'ignore_cached_errors', 'realtime']

    def __init__(self, method: str, base: str, path: str, **kwargs: dict):
        """
        The class is used to create the final URL used to fetch the data
        from the API. The parameters that are passed to the API are all in
        the GET request packet. This class will parse the `kwargs` dictionary
        and concatenate any parameters passed in.

        Parameters
        ----------
        method:
            :class:`str`: HTTP method used for the HTTP request
        base:
            :class:`str`: Base URL used for the HTTP request
        path:
            :class:`str`: URL path used for the HTTP request
        kwargs:
            :class:`dict`: Optional options used to concatenate into the final
            URL
        """
        if "#" in path:
            path = path.replace("#", "%23")

        self.method = method
        self.path = path
        self.base = base

        url = self.base + self.path

        if kwargs:
            url_params = {}
            for k, v in kwargs.items():
                if v is None:
                    continue
                if k in self.ignored_kwargs:
                    continue
                url_params[k] = v
            self.url = "{}?{}".format(url, urlencode(url_params))
        else:
            self.url = url

    @property
    def stats_key(self):
        return stats_url_matcher.sub("{}", self.path)


class HTTPClient:
    """HTTP Client for the library. All low-level requests and key-management occurs here."""

    # pylint: disable=too-many-arguments, missing-docstring, protected-access, too-many-branches
    def __init__(
            self,
            client,
            loop,
            email,
            password,
            key_names,
            key_count,
            key_scopes,
            throttle_limit,
            throttler=BasicThrottler,
            cache_max_size=10000,
            stats_max_size=1000,
            base_url="https://api.clashofclans.com/v1",
            ip=None,
            lookup_cache=True,
            update_cache=True,
            ignore_cached_errors=None,
    ):
        self.aiohttp_request_kwargs = ['params', 'data', 'json', 'cookies', 'headers', 'skip_auto_headers',
                                       'auth', 'allow_redirects', 'max_redirects', 'compress', 'chunked', 'expect100',
                                       'raise_for_status', 'read_until_eof', 'proxy', 'proxy_auth', 'timeout',
                                       'ssl', 'server_hostname', 'proxy_headers', 'trace_request_ctx', 'read_bufsize',
                                       'auto_decompress', 'max_line_size', 'max_field_size']
        self.client = client
        self.loop = loop
        self.email = email
        self.password = password
        self.key_names = key_names
        self.key_count = key_count
        self.key_scopes = key_scopes
        self.throttle_limit = throttle_limit
        per_second = key_count * throttle_limit
        self.lookup_cache = lookup_cache
        self.update_cache = update_cache
        self.ignore_cached_errors = ignore_cached_errors or []
        self.__session: Optional[aiohttp.ClientSession] = None
        self.__lock = asyncio.Semaphore(per_second)
        self.cache = cache_max_size and FIFO(cache_max_size)
        self._cache_remove_count = 0
        self.stats = stats_max_size and HTTPStats(max_size=stats_max_size)
        self.total_requests = 0
        self.total_errors = 0
        self.total_rate_limits = 0
        self.total_retries = 0
        self._last_error: Optional[str] = None
        if base_url and isinstance(base_url, str) and len(base_url) > 0:
            if base_url.endswith("/"):
                base_url = base_url[:-1]
            self.base_url = base_url
        else:
            raise ValueError("base_url must be a string and not empty.")
        self.ip = ip
        if issubclass(throttler, BasicThrottler):
            self.__throttle = throttler(1 / per_second)
        elif issubclass(throttler, BatchThrottler):
            self.__throttle = throttler(per_second)
        else:
            raise TypeError("throttler must be either BasicThrottler or BatchThrottler.")

        self._keys = []
        self.keys = None

        self.initialising_keys = asyncio.Event()
        self.initialising_keys.set()

        self.middleware = Middleware()

    @property
    def health_stats(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "total_rate_limits": self.total_rate_limits,
            "total_retries": self.total_retries,
            "last_error": self._last_error,
            "average_latency": self.stats.get_mixed_average() if self.stats else None,
            "per_endpoint": self.stats.get_all_average() if self.stats else None,
        }

    def _cache_remove(self, key):
        """Remove ``key`` from the response cache.

        ``geniuslib.utils.FIFO`` (owned by another workstream - not edited here)
        does not override ``__delitem__``, so this external ``del`` drops the value
        from ``FIFO.data`` but leaves ``key`` in FIFO's private insertion-order
        deque. Left alone, that deque drifts: it keeps growing, and a later
        eviction can pop the stale key and raise ``KeyError`` (reads tolerate it,
        but a write-triggered eviction would abort the write). The stale entry is
        therefore purged here on a best-effort basis; a real ``FIFO.__delitem__``
        in utils.py would be the permanent fix and would make this a no-op.
        """
        try:
            del self.cache[key]
            removed = True
        except KeyError:
            removed = False

        order = getattr(self.cache, "_FIFO__keys", None)
        if order is not None:
            try:
                order.remove(key)
            except ValueError:
                pass

        if not removed:
            return

        #  The following fixes a memory leak that is caused by python dicts not properly freeing disk space
        self._cache_remove_count += 1
        if self._cache_remove_count >= self.cache.max_size:
            self.cache = self.cache.copy()
            self._cache_remove_count = 0
            LOG.debug("Cache copied to prevent a memory leak")

    async def create_session(self, connector, timeout):
        # Close any previous session first: replacing it without closing would leak
        # the connector (and every keep-alive connection registered on it).
        previous = self.__session
        if previous is not None:
            await previous.close()
        self.__session = aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=timeout))

    async def close(self):
        session = self.__session
        # Null the reference so a later request raises a clear error instead of
        # using a closed session, and so a second close() is a no-op.
        self.__session = None
        if session is not None:
            await session.close()

    async def request(self, route, **kwargs):
        await self.initialising_keys.wait()

        method = route.method
        url = route.url

        if self.keys is None:
            # login() failed (its exception was raised to the caller) or was never
            # called: fail with a meaningful error instead of a TypeError from
            # ``next(None)``.
            raise InvalidCredentials(
                "API keys are not initialised; login() either failed or was never awaited."
            )

        headers = {
            "Accept"       : "application/json",
            "authorization": "Bearer {}".format(next(self.keys)),
            "Accept-Encoding": "gzip, deflate",
        }
        kwargs["headers"] = headers

        mw_req = MiddlewareRequest(method=method, url=url, headers=headers, kwargs=kwargs)
        mw_result = await self.middleware.run_request(mw_req)
        if mw_result is None:
            LOG.debug("Request aborted by middleware for %s %s", method, url)
            raise RequestAborted("Request aborted by middleware for {} {}".format(method, url))
        kwargs = mw_result.kwargs

        # ``timing_header`` stores a monotonic start time in kwargs. aiohttp must
        # never see it (it is not a valid request kwarg), so consume it here and
        # fold it into the response's elapsed_ms below.
        middleware_start = kwargs.pop("_geniuslib_start", None)

        if "json" in kwargs:
            kwargs["headers"]["Content-Type"] = "application/json"

        cache_control_key = route.url
        cache = self.cache
        lookup_cache = kwargs.pop("lookup_cache", self.lookup_cache)
        update_cache = kwargs.pop("update_cache", self.update_cache)
        ignore_cached_errors = kwargs.pop("ignore_cached_errors", self.ignore_cached_errors)
        # the cache will be cleaned once it becomes stale / a new object is available from the api.
        if isinstance(cache, FIFO) and (lookup_cache or (lookup_cache is None and 'realtime' not in url)):
            try:
                data = cache[cache_control_key]
                status_code = data.get("status_code")
                if data.get("timestamp") and data.get("timestamp") + data.get("_response_retry", 0) < datetime.now(
                        tz=timezone.utc).timestamp():
                    self._cache_remove(cache_control_key)
                elif not status_code or 200 <= status_code < 300:
                    return data
                # ignore status cached errors if wanted
                elif isinstance(ignore_cached_errors, list) and status_code in ignore_cached_errors:
                    pass
                elif status_code == 400:
                    raise InvalidArgument(400, data)
                elif status_code == 403:
                    raise Forbidden(403, data)
                elif status_code == 404:
                    raise NotFound(404, data)
                elif status_code == 503:
                    raise Maintenance(503, data)
            except KeyError:
                pass
        request_kwargs = {k: v for k, v in kwargs.items() if k in self.aiohttp_request_kwargs}
        # At most one re-authentication is attempted per request when the API says
        # our IP is not whitelisted; a second 403 raises Forbidden instead of
        # recursing forever.
        reauth_attempted = False
        for tries in range(5):
            self.total_requests += 1
            if tries > 0:
                self.total_retries += 1
            # Backoff sleeps run *after* the request lock and throttler are
            # released: sleeping while holding the semaphore would serialise
            # every other in-flight request behind this waiter for the whole
            # delay (rate-limit waits can be up to MAX_RATE_LIMIT_BACKOFF).
            backoff_delay = None
            try:
                async with self.__lock, self.__throttle:
                    start = perf_counter()
                    async with self.__session.request(method, url, **request_kwargs) as response:

                        perf = (perf_counter() - start) * 1000
                        log_info = {"method": method, "url": url, "perf_counter": perf, "status": response.status}
                        if isinstance(self.stats, HTTPStats):
                            self.stats[route.stats_key] = perf

                        LOG.debug("API HTTP Request: %s", str(log_info))
                        data = (await json_or_text(response)) or {}
                        # Cache metadata only exists on JSON objects: a 503/504 (or any
                        # other error) can come back as an HTML *string*, and assigning
                        # ``data["_response_retry"]`` on a str raised TypeError, which
                        # escaped the retry loop before the status could be handled.
                        if isinstance(data, dict):
                            data["status_code"] = response.status
                            data["timestamp"] = datetime.now(tz=timezone.utc).timestamp()
                            try:
                                # set a callback to remove the item from cache once it's stale.
                                cache_control = response.headers.get("Cache-Control", "")
                                delta = 0
                                for directive in cache_control.split(","):
                                    directive = directive.strip()
                                    if directive.startswith("max-age="):
                                        delta = int(directive.split("=", 1)[1])
                                        break
                                # encounter for changed description in cache control header. for realtime it is always
                                # 600 but that is not true. Correct is 0
                                data["_response_retry"] = delta if 'realtime' not in url else 0
                                if isinstance(cache, FIFO) and (
                                        update_cache or (update_cache is None and 'realtime' not in url)
                                ):
                                    self.cache[cache_control_key] = data
                                    LOG.debug("Cache-Control max age: %s seconds, key: %s", delta, cache_control_key)
                                    self.loop.call_later(delta, self._cache_remove, cache_control_key)

                            except (KeyError, AttributeError, ValueError):
                                # the request didn't contain cache control headers so skip any cache handling.
                                data["_response_retry"] = 0

                        if 200 <= response.status < 300:
                            LOG.debug("%s has received %s", url, data)
                            elapsed_ms = perf
                            if isinstance(middleware_start, (int, float)):
                                # timing_header was registered: report the client-observed
                                # latency (from middleware entry) instead of the bare
                                # send-to-receive window.
                                elapsed_ms = (monotonic() - middleware_start) * 1000
                            mw_resp = MiddlewareResponse(
                                status=response.status,
                                data=data,
                                headers=dict(response.headers),
                                elapsed_ms=elapsed_ms,
                                method=method,
                                url=url,
                            )
                            mw_result = await self.middleware.run_response(mw_resp)
                            if mw_result is not None:
                                data = mw_result.data
                            return data

                        if response.status == 400:
                            raise InvalidArgument(response, data)

                        if response.status == 403:
                            # ``data`` may be a str (HTML body), so reason extraction must
                            # be type-guarded instead of calling ``data.get`` blindly.
                            reason = data.get("reason") if isinstance(data, dict) else None
                            LOG.info("Forbidden (403) for %s %s: reason=%s", method, url, reason)
                            if (
                                    reason == "accessDenied.invalidIp"
                                    and self.email
                                    and self.password
                                    and not reauth_attempted
                            ):
                                reauth_attempted = True
                                LOG.info(
                                    "IP is not whitelisted; re-authenticating to refresh API keys (attempt 1/1)."
                                )
                                if self.initialising_keys.is_set():
                                    await self.initialise_keys()

                                await self.initialising_keys.wait()
                                # Rotate the bearer token for the retried attempt (the
                                # headers were built once, before the retry loop).
                                if self.keys is None:
                                    raise InvalidCredentials(
                                        "API keys are not initialised after re-authentication."
                                    )
                                if isinstance(request_kwargs.get("headers"), dict):
                                    request_kwargs["headers"]["authorization"] = "Bearer {}".format(
                                        next(self.keys)
                                    )
                                continue

                            raise Forbidden(response, data)

                        if response.status == 404:
                            raise NotFound(response, data)
                        if response.status == 429:
                            self.total_rate_limits += 1
                            self._last_error = f"rate_limited:{route.stats_key}"
                            retry_after = _parse_retry_after(response.headers.get("Retry-After"))
                            if retry_after is None:
                                backoff = (tries + 1) * 5
                            else:
                                backoff = min(retry_after, MAX_RATE_LIMIT_BACKOFF)
                            LOG.warning(
                                    "Rate-limited by the API (429) for %s. Retrying after %ss "
                                    "(attempt %d/5).", url, backoff, tries + 1
                            )
                            backoff_delay = backoff

                        elif response.status == 503:
                            if isinstance(data, str):
                                # weird case where a 503 will be raised, but html returned.
                                text = re.compile(r"<[^>]+>").sub("", data)
                                raise Maintenance(response, text)

                            raise Maintenance(response, data)

                        elif response.status in (500, 502, 504):
                            # gateway error, retry again
                            backoff_delay = tries * 2 + 1

                        else:
                            # catch any stray status codes
                            raise HTTPException(response, data)

                if backoff_delay is not None:
                    await asyncio.sleep(backoff_delay)
                    continue

            except asyncio.TimeoutError:
                self.total_errors += 1
                self._last_error = f"timeout:{route.stats_key}"
                # api timed out, retry again
                if tries > 3:
                    raise GatewayError("The API timed out waiting for the request.")

                await asyncio.sleep(tries * 2 + 1)
                continue

        else:
            # Retry budget exhausted. Label the failure accurately instead of
            # reporting every terminal status as a gateway error.
            self.total_errors += 1
            if response.status == 429:
                self._last_error = f"rate_limited:{route.stats_key}:429"
                raise RateLimitError(response, data)

            self._last_error = f"gateway_error:{route.stats_key}:{response.status}"
            if response.status in (500, 502, 504):
                if isinstance(data, str):
                    # gateway errors return HTML
                    text = re.compile(r"<[^>]+>").sub("", data)
                    raise GatewayError(response, text)

                raise GatewayError(response, data)

            if response.status == 403:
                raise Forbidden(response, data)

            raise HTTPException(response, data)

    # clans

    def search_clans(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/clans", **kwargs), **kwargs)

    def get_clan(self, tag, **kwargs):
        return self.request(Route("GET", self.base_url, "/clans/{}".format(tag)), **kwargs)

    def get_clan_members(self, tag, **kwargs):
        return self.request(Route("GET", self.base_url, "/clans/{}/members".format(tag), **kwargs), **kwargs)

    def get_clan_war_log(self, tag, **kwargs):
        return self.request(Route("GET", self.base_url, "/clans/{}/warlog".format(tag), **kwargs), **kwargs)

    def get_clan_current_war(self, tag, realtime=None, **kwargs):
        return self.request(Route("GET", self.base_url, "/clans/{}/currentwar".format(tag) + (
                                         '?realtime=true' if realtime or (realtime is None and self.client.realtime)
                                         else '')), **kwargs)

    def get_clan_war_league_group(self, tag, realtime=None, **kwargs):
        return self.request(Route("GET", self.base_url, "/clans/{}/currentwar/leaguegroup".format(tag) + (
                                         '?realtime=true' if realtime or (realtime is None and self.client.realtime)
                                         else '')), **kwargs)

    def get_cwl_wars(self, war_tag, realtime=None, **kwargs):
        return self.request(Route("GET", self.base_url, "/clanwarleagues/wars/{}".format(war_tag) + (
                                         '?realtime=true' if realtime or (realtime is None and self.client.realtime)
                                         else '')), **kwargs)

    def get_clan_raid_log(self, tag, **kwargs):
        return self.request(Route("GET", self.base_url, "/clans/{}/capitalraidseasons".format(tag), **kwargs), **kwargs)

    # locations

    def search_locations(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/locations", **kwargs), **kwargs)

    def get_location(self, location_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/locations/{}".format(location_id)), **kwargs)

    def get_location_clans(self, location_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/locations/{}/rankings/clans".format(location_id), **kwargs),
                            **kwargs)

    def get_location_players(self, location_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/locations/{}/rankings/players".format(location_id), **kwargs),
                            **kwargs)

    def get_location_clans_builder_base(self, location_id, **kwargs):
        return self.request(Route("GET", self.base_url,
                                  "/locations/{}/rankings/clans-builder-base".format(location_id), **kwargs),
                            **kwargs)

    def get_location_clans_capital(self, location_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/locations/{}/rankings/capitals".format(location_id),
                                  **kwargs), **kwargs)

    def get_location_players_builder_base(self, location_id, **kwargs):
        return self.request(Route("GET", self.base_url,
                                  "/locations/{}/rankings/players-builder-base".format(location_id), **kwargs),
                            **kwargs)

    # leagues

    def search_leagues(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/leagues", **kwargs), **kwargs)

    def search_league_tiers(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/leaguetiers", **kwargs), **kwargs)

    def search_capital_leagues(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/capitalleagues", **kwargs), **kwargs)

    def search_war_leagues(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/warleagues", **kwargs), **kwargs)

    def search_builder_base_leagues(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/builderbaseleagues", **kwargs), **kwargs)

    def get_league(self, league_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/leagues/{}".format(league_id)), **kwargs)

    def get_league_tier(self, league_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/leaguetiers/{}".format(league_id)), **kwargs)

    def get_capital_league(self, league_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/capitalleagues/{}".format(league_id)), **kwargs)

    def get_war_league(self, league_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/warleagues/{}".format(league_id)), **kwargs)

    def get_builder_base_league(self, league_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/builderbaseleagues/{}".format(league_id)), **kwargs)

    def get_league_seasons(self, league_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/leagues/{}/seasons".format(league_id), **kwargs), **kwargs)

    def get_league_season_info(self, league_id, season_id, **kwargs):
        return self.request(Route("GET", self.base_url, "/leagues/{}/seasons/{}".format(league_id, season_id),
                                  **kwargs), **kwargs)

    def get_league_group(self, league_group_tag, league_season_id, **kwargs):
        return self.request(Route("GET", self.base_url,
                                  "/leaguegroup/{}/{}".format(league_group_tag, league_season_id)), **kwargs)

    # players

    def get_player(self, player_tag, **kwargs):
        return self.request(Route("GET", self.base_url, "/players/{}".format(player_tag)), **kwargs)

    def verify_player_token(self, player_tag, token, **kwargs):
        return self.request(Route("POST", self.base_url, "/players/{}/verifytoken".format(player_tag)),
                            json={"token": token}, **kwargs)

    # labels

    def get_clan_labels(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/labels/clan", **kwargs), **kwargs)

    def get_player_labels(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/labels/players", **kwargs), **kwargs)

    def get_current_goldpass_season(self, **kwargs):
        return self.request(Route("GET", self.base_url, "/goldpass/seasons/current"), **kwargs)

    # players - battlelog / leaguehistory

    def get_player_battlelog(self, player_tag, **kwargs):
        return self.request(Route("GET", self.base_url, "/players/{}/battlelog".format(player_tag)), **kwargs)

    def get_player_league_history(self, player_tag, **kwargs):
        return self.request(Route("GET", self.base_url, "/players/{}/leaguehistory".format(player_tag)), **kwargs)

    # key updating management

    async def initialise_keys(self):
        LOG.debug("Initialising keys from the developer site.")
        self.initialising_keys.clear()

        try:
            # Use context manager to automatically clean up after ourselves.
            # The developer-site session is short-lived and has its own timeout:
            # without it aiohttp's default total timeout (300s) can hang login().
            # Note: the *client's* shared session must never be closed from in here,
            # it may be serving in-flight requests while keys are refreshed.
            async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=LOGIN_TIMEOUT_SECONDS)
            ) as session:
                body = {"email": self.email, "password": self.password}
                resp = await session.post("https://developer.clashofclans.com/api/login", json=body)
                if resp.status == 403:
                    LOG.error("Invalid credentials used when attempting to log in")
                    raise InvalidCredentials()

                LOG.info("Successfully logged into the developer site.")

                resp_payload = await resp.json()
                if not self.ip:
                    token_payload = json_loads(
                        base64_b64decode(resp_payload["temporaryAPIToken"].split(".")[1] + "====").decode("utf-8")
                    )
                    ip = token_payload["limits"][1]["cidrs"][0].split("/")[0]
                else:
                    ip = self.ip
                LOG.info("Found IP address to be %s", ip)

                resp = await session.post("https://developer.clashofclans.com/api/apikey/list")
                keys = (await resp.json()).get("keys", [])
                # Build a fresh key list instead of appending to ``self._keys``:
                # initialise_keys also runs on 403 re-authentication, and
                # appending to the previous run's keys let the list grow past
                # ``key_count`` with stale duplicates (wrong rotation matches).
                collected = []
                for key in keys:
                    # Never log the key material itself - only harmless metadata.
                    LOG.debug("Considering API key id=%s name=%s", key.get("id"), key.get("name"))
                    if key["name"] != self.key_names or ip not in key["cidrRanges"]:
                        continue
                    collected.append(key["key"])
                    if len(collected) == self.key_count:
                        break

                LOG.info("Retrieved %s valid keys from the developer site.", len(collected))

                if len(collected) < self.key_count:
                    for key in keys[:]:
                        if key["name"] != self.key_names or ip in key["cidrRanges"]:
                            continue
                        LOG.info(
                                "Deleting key with the name %s and IP %s (not matching our current IP address).",
                                self.key_names, key["cidrRanges"],
                        )
                        resp = await session.post("https://developer.clashofclans.com/api/apikey/revoke",
                                                  json={"id": key["id"]})
                        if resp.status == 200:
                            keys.remove(key)

                    while len(collected) < self.key_count and len(keys) < KEY_MAXIMUM:
                        data = {
                            "name"       : self.key_names,
                            "description": "Created on {}".format(datetime.now().strftime("%c")),
                            "cidrRanges" : [ip],
                            "scopes"     : [self.key_scopes],
                        }

                        LOG.info("Creating key with data %s.", str(data))

                        resp = await session.post("https://developer.clashofclans.com/api/apikey/create", json=data)
                        key = await resp.json()

                        if resp.status != 200:
                            LOG.error(key.get("description"))
                            raise ValueError(key.get("description"))

                        collected.append(key["key"]["key"])

                if len(keys) == 10 and len(collected) < self.key_count:
                    LOG.critical("%s keys were requested to be used, but a maximum of %s could be "
                                 "found/made on the developer site, as it has a maximum of 10 keys per account. "
                                 "Please delete some keys or lower your `key_count` level."
                                 "I will use %s keys for the life of this client.",
                                 self.key_count, len(collected), len(collected))

                if len(collected) == 0:
                    raise RuntimeError(
                            "There are {} API keys already created and none match a key_name of '{}'."
                            "Please specify a key_name kwarg, or go to 'https://developer.clashofclans.com' to delete "
                            "unused keys.".format(len(keys), self.key_names)
                    )

            # Publish atomically: only replace ``_keys`` once a complete fresh
            # set exists, so a failed (re)login leaves the previous keys usable.
            self._keys = collected
            self.keys = cycle(self._keys)
            LOG.info("Successfully initialised keys for use.")

        except Exception:
            # Re-raise: callers of login()/re-auth must see InvalidCredentials (and
            # friends) instead of a "successful" login that explodes later.
            LOG.exception("Failed to initialise keys.")
            raise
        finally:
            # Always wake up tasks parked on this event - on success *and* on
            # failure - so a failed (re)auth never deadlocks other requests.
            self.initialising_keys.set()

    def add_middleware(self, *funcs) -> None:
        """Register one or more middleware functions.

        Middleware functions should be decorated with ``@middleware('request')``
        or ``@middleware('response')``, or be async callables with a
        ``_middleware_type`` attribute.

        Parameters
        ----------
        *funcs
            Middleware functions to register.
        """
        for func in funcs:
            mw_type = getattr(func, "_middleware_type", None)
            if mw_type == "request":
                self.middleware.add_request(func)
            elif mw_type == "response":
                self.middleware.add_response(func)
            else:
                LOG.warning("Middleware %s has no _middleware_type; skipping", func)

    def remove_middleware(self, *funcs) -> None:
        """Remove one or more middleware functions."""
        for func in funcs:
            mw_type = getattr(func, "_middleware_type", None)
            if mw_type == "request":
                self.middleware.remove_request(func)
            elif mw_type == "response":
                self.middleware.remove_response(func)

    async def get_data_from_url(self, url):
        """Download raw bytes from ``url`` (used to save badges/icons/images).

        The URL comes from an API payload, so it is validated before use: only
        ``https://`` URLs whose host is ``clashofclans.com`` or ``supercell.com``
        (or a subdomain of either) are fetched. That blocks scheme confusion
        (``file://``, ``http://``) and SSRF against arbitrary or internal hosts.
        Extend ``ALLOWED_ASSET_HOSTS``/``ALLOWED_ASSET_HOST_SUFFIXES`` if Supercell
        starts serving these assets from another domain.

        Raises
        ------
        ClashOfClansException
            The client has no open HTTP session (login() was not called or was closed).
        InvalidArgument
            The URL is not an ``https://`` URL on an allowed Supercell/Clash host.
        NotFound, HTTPException
            The remote server answered with an error status.
        """
        session = self.__session
        if session is None:
            raise ClashOfClansException(
                "Cannot fetch {!r}: the HTTP session is closed or was never created.".format(url)
            )

        # Follow redirects manually so each hop is re-validated against the
        # allowlist. auto-following (allow_redirects=True) would let a trusted
        # host bounce us to an arbitrary/internal target without revalidation.
        current = url
        for _ in range(MAX_ASSET_REDIRECTS):
            parsed = urlparse(current) if isinstance(current, str) else None
            if parsed is None or parsed.scheme != "https" or not _is_allowed_asset_host(parsed.hostname):
                raise InvalidArgument(
                    "Refusing to fetch {!r}: only https URLs on clashofclans.com/supercell.com are allowed.".format(url)
                )
            async with session.get(current, allow_redirects=False) as response:
                if response.status == 200:
                    return await response.read()
                if response.status in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location")
                    if not location:
                        break
                    current = urljoin(current, location)
                    continue
                if response.status == 404:
                    raise NotFound(response, "image not found")
                raise HTTPException(response, "failed to get image")

        raise HTTPException(response, "too many redirects")
