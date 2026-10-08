"""Regression tests for the HTTP layer: retries, re-auth, login, and URL guards.

Covers the fixes shipped to ``geniuslib/http.py``, ``geniuslib/middleware.py``
and ``geniuslib/errors.py``:

* ``initialise_keys`` - 15s login timeout, no session teardown, safe logging,
  exception propagation and waiter release via ``finally``.
* Retry loop - 403 re-authentication (max 1), 429 ``Retry-After`` handling,
  HTML error bodies no longer raising ``TypeError``.
* ``get_data_from_url`` - https/Supercell host allowlist (no SSRF).
* Middleware - ``Response.method``/``Response.url``, ``_geniuslib_start``
  consumption, ``RequestAborted``.
* ``HTTPException.__slots__`` all populated.

All HTTP calls are served by fakes - no network traffic.
"""

import asyncio
import base64
import json as jsonlib
import logging
from itertools import cycle
from time import monotonic as real_monotonic
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import orjson
import pytest

from geniuslib import http as http_module
from geniuslib.errors import (
    ClashOfClansException,
    Forbidden,
    HTTPException,
    InvalidArgument,
    InvalidCredentials,
    Maintenance,
    NotFound,
    RateLimitError,
    RequestAborted,
)
from geniuslib.http import (
    BatchThrottler,
    HTTPClient,
    Route,
    _is_allowed_asset_host,
    _parse_retry_after,
    json_or_text,
)
from geniuslib.middleware import middleware, response_logger, timing_header

BASE = "https://api.clashofclans.com/v1"


def route(path="/clans/%23TEST"):
    """Standard route used throughout the tests."""
    return Route("GET", BASE, path)


def make_http(**overrides):
    """Construct an HTTPClient with network-free knobs and no API keys set."""
    opts = dict(
        client=MagicMock(),
        loop=MagicMock(),
        email="user@example.com",
        password="SECRET_PASSWORD",
        key_names="genius-test",
        key_count=1,
        key_scopes="clash",
        throttle_limit=30,
        throttler=BatchThrottler,
        cache_max_size=0,
        base_url=BASE,
    )
    opts.update(overrides)
    http = HTTPClient(**opts)
    http.initialising_keys.set()
    return http


def ready_http(**overrides):
    """make_http + a single usable API key cycle."""
    http = make_http(**overrides)
    http._keys = ["TESTKEY"]
    http.keys = cycle(http._keys)
    return http


class FakeResponse(aiohttp.ClientResponse):
    """aiohttp.ClientResponse stand-in with no real transport.

    Subclasses ClientResponse so ``HTTPException._from_response`` recognises it
    and copies ``status``/``headers`` onto the raised exception.
    """

    def __init__(self, status=200, payload=None, headers=None, body=None):
        self._cache = {}
        self.status = status
        self._headers = dict(headers or {})
        self._payload = payload
        self._body = body

    async def json(self, loads=None, **kwargs):
        if isinstance(self._payload, BaseException):
            raise self._payload
        return self._payload

    async def text(self, encoding="utf-8"):
        if isinstance(self._body, BaseException):
            raise self._body
        if self._body is not None:
            return self._body
        return orjson.dumps(self._payload or {}).decode("utf-8")

    async def read(self):
        if isinstance(self._body, BaseException):
            raise self._body
        return self._body


class ContextManager:
    """Makes a FakeResponse usable as ``async with session.get(...) as resp``."""

    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, *exc):
        return False


class FakeSession:
    """Minimal aiohttp.ClientSession stand-in recording calls for assertions."""

    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.calls = []
        self.closed = False

    def _next(self):
        if not self.responses:
            return FakeResponse(200, {})
        if len(self.responses) > 1:
            return self.responses.pop(0)
        return self.responses[0]

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return ContextManager(self._next())

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return ContextManager(self._next())

    async def close(self):
        self.closed = True


class FakeLoginSession:
    """aiohttp.ClientSession stand-in for the developer-site login flow."""

    def __init__(self, posts):
        self.posts = list(posts)
        self.post_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, **kwargs):
        self.post_calls.append((url, kwargs))
        if len(self.posts) > 1:
            return self.posts.pop(0)
        return self.posts[0]


def install_session(http, session):
    http._HTTPClient__session = session
    return session


def patch_client_session(monkeypatch, factory):
    """Point ``geniuslib.http`` at a fake aiohttp.ClientSession factory."""
    monkeypatch.setattr(http_module.aiohttp, "ClientSession", factory)


def patch_sleep(monkeypatch):
    """Replace ``asyncio.sleep`` in the http module with a recorder."""
    sleeps = []

    async def fake_sleep(delay):
        sleeps.append(delay)

    return sleeps, monkeypatch.setattr(http_module.asyncio, "sleep", fake_sleep)


class TestJsonOrText:
    async def test_returns_parsed_json(self):
        resp = FakeResponse(200, {"name": "TestClan"})
        assert await json_or_text(resp) == {"name": "TestClan"}

    async def test_content_type_error_falls_back_to_text(self):
        request_info = MagicMock()
        request_info.url = "https://api.clashofclans.com/v1/x"
        resp = FakeResponse(
            200,
            aiohttp.ContentTypeError(request_info=request_info, history=()), body="<html>oops</html>",
        )
        assert await json_or_text(resp) == "<html>oops</html>"

    async def test_malformed_json_falls_back_to_text(self):
        resp = FakeResponse(200, ValueError("Expecting value"), body="not json")
        assert await json_or_text(resp) == "not json"

    async def test_orjson_decoder_error_falls_back_to_text(self):
        resp = FakeResponse(200, orjson.JSONDecodeError("Expecting value", "", 0), body="[]")
        assert await json_or_text(resp) == "[]"


class TestRoute:
    def test_ignores_client_only_kwargs_in_url(self):
        r = route("/clans/#TEST")
        assert r.url == BASE + "/clans/%23TEST"

    def test_realtime_and_cache_flags_not_serialized(self):
        r = Route("GET", BASE, "/clans/%23TEST", realtime=True, lookup_cache=False, limit=10)
        assert "realtime" not in r.url
        assert "lookup_cache" not in r.url
        assert "limit=10" in r.url


class TestRetryHelpers:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("7", 7),
            (" 7 ", 7),
            ("0", 0),
            (7, 7),
            (None, None),
            ("", None),
            ("abc", None),
            ("Wed, 21 Oct 2015 07:28:00 GMT", None),
        ],
    )
    def test_parse_retry_after(self, value, expected):
        assert _parse_retry_after(value) == expected

    @pytest.mark.parametrize(
        "host,expected",
        [
            ("clashofclans.com", True),
            ("supercell.com", True),
            ("static.supercell.com", True),
            ("api.clashofclans.com", True),
            ("clashofclans.com.", True),
            ("CLASHOFCLANS.COM", True),
            ("evil.com", False),
            ("evilclashofclans.com", False),
            ("clashofclans.com.evil.com", False),
            ("", False),
            (None, False),
        ],
    )
    def test_is_allowed_asset_host(self, host, expected):
        assert _is_allowed_asset_host(host) is expected


class TestCacheRemove:
    def test_removes_value_and_purges_fifo_deque(self):
        http = make_http(cache_max_size=10)
        http.cache["a"] = {"x": 1}
        http.cache["b"] = {"x": 2}
        assert list(http.cache._FIFO__keys) == ["a", "b"]

        http._cache_remove("a")

        assert "a" not in http.cache.data
        assert list(http.cache._FIFO__keys) == ["b"]
        assert "b" in http.cache.data

    def test_cache_remove_is_idempotent(self):
        http = make_http(cache_max_size=10)
        http.cache["a"] = {"x": 1}
        http._cache_remove("a")
        http._cache_remove("a")
        assert list(http.cache._FIFO__keys) == []
        assert http._cache_remove_count == 1


class TestRequestBasics:
    async def test_success_returns_parsed_json(self):
        http = ready_http()
        session = install_session(http, FakeSession([FakeResponse(200, {"name": "TestClan"})]))

        result = await http.request(route())

        assert result["name"] == "TestClan"
        assert session.calls[0][0] == "GET"
        assert session.calls[0][1].startswith(BASE)
        assert "authorization" in session.calls[0][2]["headers"]

    async def test_no_keys_raises_invalid_credentials(self):
        http = make_http()
        with pytest.raises(InvalidCredentials):
            await http.request(route())

    async def test_request_waits_for_initialising_keys(self):
        http = ready_http()
        install_session(http, FakeSession([FakeResponse(200, {"ok": True})]))
        http.initialising_keys.clear()

        task = asyncio.ensure_future(http.request(route()))
        await asyncio.sleep(0)
        assert not task.done()

        http.initialising_keys.set()
        result = await asyncio.wait_for(task, 1)
        assert result["ok"] is True

    async def test_middleware_abort_raises_request_aborted(self):
        http = ready_http()
        session = install_session(http, FakeSession())

        @middleware("request")
        async def abort(req):
            return None

        http.add_middleware(abort)

        with pytest.raises(RequestAborted):
            await http.request(route())
        assert session.calls == []


class TestErrorBodies:
    async def test_html_503_raises_maintenance_without_typeerror(self):
        http = ready_http()
        install_session(http, FakeSession([FakeResponse(503, ValueError("bad"), body="<html>Down</html>")]))

        with pytest.raises(Maintenance) as excinfo:
            await http.request(route())

        assert excinfo.value.status == 503
        assert "<" not in str(excinfo.value)

    async def test_html_403_raises_forbidden_without_attributeerror(self):
        http = ready_http()
        http.initialise_keys = AsyncMock()
        install_session(http, FakeSession([FakeResponse(403, ValueError("bad"), body="<html>Denied</html>")]))

        with pytest.raises(Forbidden) as excinfo:
            await http.request(route())

        assert excinfo.value.status == 403
        http.initialise_keys.assert_not_awaited()

    async def test_404_raises_not_found(self):
        http = ready_http()
        install_session(http, FakeSession([FakeResponse(404, {"reason": "notFound"})]))

        with pytest.raises(NotFound) as excinfo:
            await http.request(route())

        assert excinfo.value.status == 404
        assert excinfo.value.reason == "notFound"


class TestRateLimit:
    async def test_429_honours_retry_after_then_rate_limit_error(self, monkeypatch):
        http = ready_http()
        install_session(
            http,
            FakeSession([FakeResponse(429, {}, headers={"Retry-After": "7"})]),
        )
        sleeps, _undone = patch_sleep(monkeypatch)

        with pytest.raises(RateLimitError) as excinfo:
            await http.request(route())

        assert sleeps == [7, 7, 7, 7, 7]
        assert isinstance(excinfo.value, RateLimitError)
        assert isinstance(excinfo.value, HTTPException)
        assert excinfo.value.status == 429
        assert http.total_rate_limits == 5
        assert http.total_retries == 4
        assert http._last_error.startswith("rate_limited:")

    async def test_429_http_date_retry_after_falls_back_to_progressive(self, monkeypatch):
        http = ready_http()
        install_session(
            http,
            FakeSession([FakeResponse(429, {}, headers={"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"})]),
        )
        sleeps, _undone = patch_sleep(monkeypatch)

        with pytest.raises(RateLimitError):
            await http.request(route())

        assert sleeps == [5, 10, 15, 20, 25]

    async def test_429_backoff_sleeps_with_request_lock_released(self, monkeypatch):
        """FIX-20b: the 429 backoff must not park while holding the request lock."""
        http = ready_http()
        install_session(
            http,
            FakeSession([FakeResponse(429, {}, headers={"Retry-After": "7"})]),
        )
        lock = http._HTTPClient__lock
        permits_when_free = lock._value
        observed = []

        async def fake_sleep(delay):
            # While the requester is parked in the backoff wait, record how many
            # semaphore permits are still available: fewer than the initial value
            # means the request lock is held during the sleep and every other
            # in-flight request is serialised behind this waiter.
            observed.append((delay, lock._value))

        monkeypatch.setattr(http_module.asyncio, "sleep", fake_sleep)

        with pytest.raises(RateLimitError):
            await http.request(route())

        assert observed, "backoff sleep never happened"
        assert [delay for delay, _ in observed] == [7, 7, 7, 7, 7]
        held = [permits for _, permits in observed if permits != permits_when_free]
        assert held == [], "request lock was held during backoff sleeps: {}".format(held)


class TestReauthentication:
    def _invalid_ip_payload(self):
        return {"reason": "accessDenied.invalidIp"}

    async def test_single_reauth_rotates_token_and_retries(self):
        http = ready_http()
        session = install_session(
            http,
            FakeSession([FakeResponse(403, self._invalid_ip_payload()), FakeResponse(200, {"ok": True})]),
        )

        async def rotate_keys():
            http.keys = cycle(["ROTATED_KEY"])

        http.initialise_keys = AsyncMock(side_effect=rotate_keys)

        result = await http.request(route())

        assert result["ok"] is True
        assert http.initialise_keys.await_count == 1
        assert session.calls[1][2]["headers"]["authorization"] == "Bearer ROTATED_KEY"
        assert http.total_retries == 1

    async def test_permanent_invalid_ip_raises_forbidden_after_one_reauth(self):
        http = ready_http()
        install_session(http, FakeSession([FakeResponse(403, self._invalid_ip_payload())]))
        http.initialise_keys = AsyncMock()

        with pytest.raises(Forbidden) as excinfo:
            await http.request(route())

        assert excinfo.value.status == 403
        assert http.initialise_keys.await_count == 1
        assert http.total_requests == 2

    async def test_403_with_other_reason_does_not_reauth(self):
        http = ready_http()
        install_session(http, FakeSession([FakeResponse(403, {"reason": "accessDenied.invalidSession"})]))
        http.initialise_keys = AsyncMock()

        with pytest.raises(Forbidden):
            await http.request(route())

        http.initialise_keys.assert_not_awaited()


class TestTiming:
    async def test_timing_header_start_is_consumed_and_reported(self):
        http = ready_http()
        install_session(http, FakeSession([FakeResponse(200, {"ok": True})]))
        captured = {}

        @middleware("request")
        async def backdate(req):
            req.kwargs["_geniuslib_start"] = real_monotonic() - 2.0
            return req

        @middleware("response")
        async def capture(resp):
            captured.update(elapsed_ms=resp.elapsed_ms, method=resp.method, url=resp.url, status=resp.status)
            return resp

        http.add_middleware(timing_header, backdate, capture)

        result = await http.request(route())

        assert result["ok"] is True
        assert captured["method"] == "GET"
        assert captured["url"] == BASE + "/clans/%23TEST"
        assert captured["status"] == 200
        assert captured["elapsed_ms"] >= 1900

    async def test_response_logger_includes_method_url_status(self, caplog):
        http = ready_http()
        install_session(http, FakeSession([FakeResponse(200, {"ok": True})]))
        http.add_middleware(response_logger)

        with caplog.at_level(logging.DEBUG, logger="geniuslib.middleware"):
            await http.request(route())

        assert "<<< GET" in caplog.text
        assert BASE + "/clans/%23TEST" in caplog.text
        assert "status=200" in caplog.text


class TestSessionLifecycle:
    async def test_create_session_closes_previous_and_close_is_idempotent(self):
        http = ready_http()

        await http.create_session(None, 5.0)
        first = http._HTTPClient__session
        assert first is not None and not first.closed

        await http.create_session(None, 5.0)
        second = http._HTTPClient__session
        assert first.closed is True
        assert second is not first and not second.closed

        await http.close()
        assert second.closed is True
        assert http._HTTPClient__session is None

        await http.close()
        assert http._HTTPClient__session is None

    async def test_fake_session_close_is_idempotent(self):
        http = ready_http()
        session = install_session(http, FakeSession([FakeResponse(200, {"ok": True})]))
        await http.close()
        assert session.closed is True
        assert http._HTTPClient__session is None
        await http.close()


class TestInitialiseKeys:
    def _token(self):
        payload = jsonlib.dumps({"limits": [{}, {"cidrs": ["203.0.113.5/32"]}]}).encode("utf-8")
        segment = base64.b64encode(payload).decode("ascii").rstrip("=")
        return "header.{}.signature".format(segment)

    def _session_factory(self, session):
        def factory(*args, **kwargs):
            return MagicMock(
                __aenter__=AsyncMock(return_value=session),
                __aexit__=AsyncMock(return_value=False),
            )

        return factory

    async def test_login_success_sets_event_with_15s_timeout(self, monkeypatch, caplog):
        http = make_http()
        http.close = MagicMock()

        key_entry = {
            "id": 7,
            "name": "genius-test",
            "cidrRanges": ["203.0.113.5"],
            "key": "KEY_SUPERSECRET",
        }
        posts = [
            FakeResponse(200, {"temporaryAPIToken": self._token()}),
            FakeResponse(200, {"keys": [key_entry]}),
        ]
        session = FakeLoginSession(posts)
        captured = {}
        factory = self._session_factory(session)

        def recording_factory(*args, **kwargs):
            captured.update(kwargs)
            return factory(*args, **kwargs)

        patch_client_session(monkeypatch, recording_factory)

        with caplog.at_level(logging.DEBUG, logger="geniuslib.http"):
            await http.initialise_keys()

        assert captured["timeout"].total == 15
        assert http.initialising_keys.is_set()
        assert next(http.keys) == "KEY_SUPERSECRET"
        http.close.assert_not_called()
        assert "KEY_SUPERSECRET" not in caplog.text
        assert "SECRET_PASSWORD" not in caplog.text
        assert "Considering API key id=7" in caplog.text

    async def test_login_invalid_credentials_propagates_and_sets_event(self, monkeypatch):
        http = make_http()
        http.close = MagicMock()
        session = FakeLoginSession([FakeResponse(403, {"reason": "invalidCredentials"})])
        patch_client_session(monkeypatch, self._session_factory(session))

        with pytest.raises(InvalidCredentials):
            await http.initialise_keys()

        assert http.initialising_keys.is_set()
        assert http.keys is None
        http.close.assert_not_called()

    async def test_login_no_matching_key_raises_runtime_error(self, monkeypatch):
        http = make_http(ip="198.51.100.7")
        full_keys = [
            {
                "id": i,
                "name": "unrelated-{}".format(i),
                "cidrRanges": ["198.51.100.1"],
                "key": "KEY-{}".format(i),
            }
            for i in range(10)
        ]
        posts = [
            FakeResponse(200, {"temporaryAPIToken": "unused"}),
            FakeResponse(200, {"keys": full_keys}),
        ]
        session = FakeLoginSession(posts)
        patch_client_session(monkeypatch, self._session_factory(session))

        with pytest.raises(RuntimeError):
            await http.initialise_keys()

        assert http.initialising_keys.is_set()
        assert http.keys is None

    async def test_login_unexpected_error_releases_waiters(self, monkeypatch):
        http = make_http()

        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        patch_client_session(monkeypatch, boom)

        with pytest.raises(RuntimeError, match="boom"):
            await http.initialise_keys()

        assert http.initialising_keys.is_set()

    async def test_repeated_initialise_keys_stays_bounded_by_key_count(self, monkeypatch):
        """FIX-20c: re-authentication must rebuild ``_keys``, not accumulate."""
        http = make_http(ip="203.0.113.5", key_count=1)
        entries = [
            {"id": 1, "name": "genius-test", "cidrRanges": ["203.0.113.5"], "key": "K1"},
            {"id": 2, "name": "genius-test", "cidrRanges": ["203.0.113.5"], "key": "K2"},
        ]

        def factory(*args, **kwargs):
            session = FakeLoginSession(
                [
                    FakeResponse(200, {"temporaryAPIToken": "unused"}),
                    FakeResponse(200, {"keys": entries}),
                ]
            )
            return MagicMock(
                __aenter__=AsyncMock(return_value=session),
                __aexit__=AsyncMock(return_value=False),
            )

        patch_client_session(monkeypatch, factory)

        await http.initialise_keys()
        assert len(http._keys) == http.key_count

        await http.initialise_keys()
        await http.initialise_keys()

        assert len(http._keys) == http.key_count
        assert http._keys == ["K1"]
        assert next(http.keys) == "K1"


class TestGetDataFromUrl:
    @pytest.mark.parametrize(
        "url",
        [
            "file:///etc/passwd",
            "http://evil.com/x.png",
            "https://evil.com/x.png",
            "ftp://static.supercell.com/x.png",
            "https://clashofclans.com.evil.com/x.png",
            "relative/path.png",
            None,
        ],
    )
    async def test_rejects_disallowed_urls_without_network(self, url):
        http = make_http()
        session = install_session(http, FakeSession())

        with pytest.raises(InvalidArgument):
            await http.get_data_from_url(url)

        assert session.calls == []

    async def test_no_session_raises_clear_error(self):
        http = make_http()
        with pytest.raises(ClashOfClansException):
            await http.get_data_from_url("https://static.supercell.com/x.png")

    async def test_fetches_allowed_subdomain(self):
        http = make_http()
        session = install_session(http, FakeSession([FakeResponse(200, body=b"image-bytes")]))

        result = await http.get_data_from_url("https://static.supercell.com/badges/x.png")

        assert result == b"image-bytes"
        assert session.calls[0][1] == "https://static.supercell.com/badges/x.png"

    async def test_fetches_allowed_apex_host(self):
        http = make_http()
        session = install_session(http, FakeSession([FakeResponse(200, body=b"image-bytes")]))

        result = await http.get_data_from_url("https://clashofclans.com/x.png")

        assert result == b"image-bytes"
        assert session.calls[0][1] == "https://clashofclans.com/x.png"

    async def test_404_raises_not_found(self):
        http = make_http()
        install_session(http, FakeSession([FakeResponse(404, body=b"")]))

        with pytest.raises(NotFound):
            await http.get_data_from_url("https://static.supercell.com/x.png")

    async def test_other_status_raises_http_exception(self):
        http = make_http()
        install_session(http, FakeSession([FakeResponse(500, body=b"")]))

        with pytest.raises(HTTPException):
            await http.get_data_from_url("https://static.supercell.com/x.png")


class TestExceptionSlots:
    def test_http_exception_slots_all_populated(self):
        exc = HTTPException(403, {"reason": "forbidden", "message": "nope"})
        for slot in HTTPException.__slots__:
            assert hasattr(exc, slot), slot
        assert exc.status == 403
        assert exc.reason == "forbidden"
        assert exc.message == "nope"

    def test_http_exception_from_string_data(self):
        exc = HTTPException(404, "image not found")
        assert exc.status == 404
        assert exc.reason == "image not found"
        assert exc.message is None

    def test_http_exception_from_response_object(self):
        exc = HTTPException(FakeResponse(502, {}), {"reason": "bad gateway"})
        assert exc.status == 502
        assert exc.response is not None
        assert exc.reason == "bad gateway"

    def test_http_exception_default_init(self):
        exc = HTTPException()
        for slot in HTTPException.__slots__:
            assert hasattr(exc, slot), slot
        assert exc.status == 0
        assert exc.response is None
