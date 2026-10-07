"""Regression tests for the async-layer audit fixes.

Covers: ExtendedEnum hashing, TaggedIterator key-rotation error paths,
EventsClient poller looping/backoff/eviction/dispatch, the CLI password and
CSV handling, and consistency of the events.pyi type stub.
"""

import ast
import asyncio
import csv
import io
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

import geniuslib
from geniuslib import cli, events
from geniuslib.enums import Role, WarState
from geniuslib.events import EventsClient
from geniuslib.iterators import TaggedIterator

# ---------------------------------------------------------------------------
# enums: __hash__ restored alongside value-based __eq__
# ---------------------------------------------------------------------------

def test_extended_enum_members_are_hashable():
    assert hash(Role.member) == hash(Role.member)
    assert len({Role.member, Role.elder, Role.member}) == 2

    mapping = {Role.leader: "leader-role"}
    assert mapping[Role.leader] == "leader-role"

    assert hash(WarState.in_war) == hash(WarState.in_war)
    assert len({WarState.in_war, WarState.war_ended, WarState.in_war}) == 2

    # value-based equality still works, and hashing stays consistent with it
    assert Role.elder == "admin"
    assert hash(Role.elder) == hash("admin")
    assert Role.member != Role.elder


# ---------------------------------------------------------------------------
# iterators: honest KeyError when keys cannot be rotated
# ---------------------------------------------------------------------------

class _BareClient:
    """A client exposing neither reset_keys() nor an http layer."""


class _FakeHttp:
    def __init__(self, email=None, password=None):
        self.email = email
        self.password = password
        self._keys = []
        self.initialise_calls = 0

    async def initialise_keys(self):
        self.initialise_calls += 1
        self._keys = ["key-1"]


class _FakeHttpClient:
    def __init__(self, email=None, password=None):
        self.http = _FakeHttp(email=email, password=password)


async def test_iterator_keyerror_without_reset_support_raises_keyerror():
    iterator = TaggedIterator(_BareClient(), ["#TAG"], None)

    async def boom(tag, **kwargs):
        raise KeyError("no keys left")

    iterator.get_method = boom

    with pytest.raises(KeyError):
        await iterator._next()


async def test_iterator_rotates_keys_via_http_initialise_keys():
    client = _FakeHttpClient(email="dev@example.com", password="secret")
    iterator = TaggedIterator(client, ["#TAG"], None)

    state = {"fail": True}

    async def get(tag, **kwargs):
        if state["fail"]:
            state["fail"] = False
            raise KeyError("no keys left")
        return f"object-{tag}"

    iterator.get_method = get

    assert await iterator._next() == "object-#TAG"
    assert client.http.initialise_calls == 1
    assert client.http._keys == ["key-1"]


async def test_iterator_without_credentials_reraises_keyerror():
    client = _FakeHttpClient(email=None, password=None)
    iterator = TaggedIterator(client, ["#TAG"], None)

    async def boom(tag, **kwargs):
        raise KeyError("no keys left")

    iterator.get_method = boom

    with pytest.raises(KeyError):
        await iterator._next()
    assert client.http.initialise_calls == 0


async def test_iterator_prefers_client_reset_keys_when_available():
    class CustomClient:
        def __init__(self):
            self.reset_calls = 0

        async def reset_keys(self):
            self.reset_calls += 1
            return True

    client = CustomClient()
    iterator = TaggedIterator(client, ["#TAG"], None)

    state = {"fail": True}

    async def get(tag, **kwargs):
        if state["fail"]:
            state["fail"] = False
            raise KeyError("exhausted")
        return "ok"

    iterator.get_method = get

    assert await iterator._next() == "ok"
    assert client.reset_calls == 1


async def test_iterator_failed_reset_reraises_keyerror():
    class FailingResetClient:
        async def reset_keys(self):
            return False

    iterator = TaggedIterator(FailingResetClient(), ["#TAG"], None)

    async def boom(tag, **kwargs):
        raise KeyError("no keys left")

    iterator.get_method = boom

    with pytest.raises(KeyError):
        await iterator._next()


# ---------------------------------------------------------------------------
# events: pollers loop instead of recursing, backoff is capped
# ---------------------------------------------------------------------------

async def test_season_poller_loops_instead_of_recursing(monkeypatch):
    client = EventsClient(loop=asyncio.get_running_loop())
    monkeypatch.setattr(events, "DEFAULT_SLEEP", 0)

    dispatched = []
    client.dispatch = lambda *args, **kwargs: dispatched.append(args)

    attempts = {"count": 0}

    def flaky_season_end():
        attempts["count"] += 1
        if attempts["count"] >= 1200:
            raise asyncio.CancelledError
        raise RuntimeError("season lookup failed")

    monkeypatch.setattr(events, "get_season_end", flaky_season_end)

    # the old implementation recursed on every failure and hit RecursionError
    # long before ~1200 iterations
    await client._end_of_season_poller()

    assert attempts["count"] == 1200
    assert dispatched and dispatched[0][0] == "event_error"


async def test_poller_backoff_is_capped(monkeypatch):
    client = EventsClient(loop=asyncio.get_running_loop())
    real_asyncio = asyncio
    delays = []

    class AsyncioStub:
        """Delegates to the real asyncio module but records sleep delays."""

        def __getattr__(self, name):
            return getattr(real_asyncio, name)

        async def sleep(self, delay):
            delays.append(delay)

    monkeypatch.setattr(events, "asyncio", AsyncioStub())
    monkeypatch.setattr(events, "DEFAULT_SLEEP", 10)
    monkeypatch.setattr(events, "MAX_BACKOFF", 40)
    client.dispatch = lambda *args, **kwargs: None

    attempts = {"count": 0}

    def broken_season_end():
        attempts["count"] += 1
        if attempts["count"] > 40:
            raise real_asyncio.CancelledError
        raise RuntimeError("always fails")

    monkeypatch.setattr(events, "get_season_end", broken_season_end)

    await client._end_of_season_poller()

    assert attempts["count"] == 41
    assert delays[0] == 10
    assert max(delays) == 40
    assert set(delays) <= {10, 20, 40}


# ---------------------------------------------------------------------------
# events: loop rebinding and run_forever shutdown
# ---------------------------------------------------------------------------

async def test_prepare_loop_rebinds_stale_loop():
    stale = asyncio.new_event_loop()
    client = EventsClient(loop=stale)
    try:
        client._prepare_loop()
        assert client.loop is asyncio.get_running_loop()
    finally:
        stale.close()


def test_run_forever_closes_client_after_keyboard_interrupt(caplog):
    loop = asyncio.new_event_loop()
    client = EventsClient(loop=loop)

    closed = []
    original_close = client.close

    async def spy_close():
        closed.append(True)
        await original_close()

    client.close = spy_close

    def raise_interrupt():
        raise KeyboardInterrupt

    loop.call_soon(raise_interrupt)

    with caplog.at_level(logging.WARNING, logger="geniuslib.events"):
        try:
            client.run_forever()
        finally:
            loop.close()

    assert closed == [True]
    assert any("no updater tasks" in record.getMessage() for record in caplog.records)


# ---------------------------------------------------------------------------
# events: dispatch logs failures instead of printing tracebacks
# ---------------------------------------------------------------------------

async def test_dispatch_listener_failure_logs_without_printing(caplog, capsys):
    client = EventsClient(loop=asyncio.get_running_loop())

    async def broken_listener():
        raise RuntimeError("listener exploded")

    client._listeners["client"]["custom_event"] = [broken_listener]

    with caplog.at_level(logging.ERROR, logger="geniuslib.events"):
        client.dispatch("custom_event")
        await asyncio.sleep(0.05)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    errors = [record for record in caplog.records if record.levelno == logging.ERROR]
    assert errors, "expected an ERROR log for the failing listener"
    assert errors[0].exc_info is not None


async def test_dispatch_event_error_logs_exception(caplog, capsys):
    client = EventsClient(loop=asyncio.get_running_loop())
    error = RuntimeError("poller failed")

    with caplog.at_level(logging.ERROR, logger="geniuslib.events"):
        client.dispatch("event_error", error)
        await asyncio.sleep(0)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    errors = [record for record in caplog.records if record.levelno == logging.ERROR]
    assert errors, "expected an ERROR log for event_error"
    assert errors[0].exc_info is not None
    assert errors[0].exc_info[1] is error


# ---------------------------------------------------------------------------
# events: cache eviction protects watched tags and behaves like an LRU
# ---------------------------------------------------------------------------

class _Tagged:
    def __init__(self, tag):
        self.tag = tag


async def test_eviction_protects_watched_tags_and_is_lru():
    client = EventsClient(loop=asyncio.get_running_loop())
    client._data_maxsize = 3
    client.add_clan_updates("#WATCH")

    client._update_clan(_Tagged("#A"))
    client._update_clan(_Tagged("#B"))
    client._update_clan(_Tagged("#C"))
    client._update_clan(_Tagged("#WATCH"))

    # oldest unprotected entry goes first; the watched tag stays
    assert "#A" not in client._clans
    assert {"#B", "#C", "#WATCH"} == set(client._clans)

    # touching #B moves it to the back of the eviction queue
    assert client._get_cached_clan("#B") is not None
    client._update_clan(_Tagged("#D"))

    assert "#C" not in client._clans
    assert {"#B", "#D", "#WATCH"} == set(client._clans)
    assert "#WATCH" in client._clans

    # when every entry is watched, nothing is evicted (by design)
    client.add_clan_updates("#B", "#D", "#WATCH2")
    client._update_clan(_Tagged("#WATCH2"))
    assert {"#WATCH", "#B", "#D", "#WATCH2"} == set(client._clans)


# ---------------------------------------------------------------------------
# CLI: password precedence, client closure, truncation, CSV quoting
# ---------------------------------------------------------------------------

def test_password_resolution_precedence(monkeypatch):
    monkeypatch.setenv("GENIUSLIB_PASSWORD", "env-password")

    flagged = SimpleNamespace(email="dev@example.com", password="flag-password", token=None)
    with pytest.warns(FutureWarning, match="--password"):
        assert cli._resolve_password(flagged) == "flag-password"

    from_env = SimpleNamespace(email="dev@example.com", password=None, token=None)
    assert cli._resolve_password(from_env) == "env-password"

    monkeypatch.delenv("GENIUSLIB_PASSWORD")
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: "prompted-password")
    assert cli._resolve_password(from_env) == "prompted-password"

    no_email = SimpleNamespace(email=None, password=None, token=None)
    assert cli._resolve_password(no_email) is None


async def test_login_failure_closes_client(monkeypatch):
    instances = []

    class FailingClient:
        def __init__(self):
            self.closed = False
            instances.append(self)

        async def login(self, email, password):
            raise RuntimeError("bad credentials")

        async def login_with_tokens(self, *tokens):
            raise AssertionError("token login should not be used here")

        async def close(self):
            self.closed = True

    monkeypatch.setattr(cli, "Client", FailingClient)
    monkeypatch.setenv("GENIUSLIB_PASSWORD", "pw")
    args = SimpleNamespace(email="dev@example.com", password=None, token=None)

    with pytest.raises(RuntimeError, match="bad credentials"):
        await cli._login(args)

    assert instances and instances[0].closed is True


async def test_login_without_credentials_exits_and_closes_client(monkeypatch):
    instances = []

    class FakeClient:
        def __init__(self):
            self.closed = False
            instances.append(self)

        async def close(self):
            self.closed = True

    monkeypatch.setattr(cli, "Client", FakeClient)
    monkeypatch.delenv("GENIUSLIB_PASSWORD", raising=False)
    args = SimpleNamespace(email=None, password=None, token=None)

    with pytest.raises(SystemExit):
        await cli._login(args)

    assert instances and instances[0].closed is True


def test_description_truncation():
    assert cli._truncate_description(None) == "N/A"
    assert cli._truncate_description("") == "N/A"
    assert cli._truncate_description("short") == "short"

    exactly_100 = "a" * 100
    assert cli._truncate_description(exactly_100) == exactly_100
    assert cli._truncate_description("b" * 150) == "b" * 100 + "..."


async def test_export_csv_quotes_embedded_commas(capsys):
    class FakePlayer:
        _raw_data = {
            "tag": "#2PP",
            "name": "Name, With Comma",
            "townHallLevel": 16,
            "trophies": 5200,
            "expLevel": 200,
            "clan": {"name": "Clan, Name"},
        }

    class FakeClient:
        async def get_player(self, tag):
            return FakePlayer()

    args = SimpleNamespace(type="player", tag="#2PP", format="csv")
    await cli._cmd_export(FakeClient(), args)

    out = capsys.readouterr().out
    rows = list(csv.reader(io.StringIO(out)))
    assert rows[0] == ["tag", "name", "town_hall", "trophies", "exp_level", "clan"]
    assert rows[1] == ["#2PP", "Name, With Comma", "16", "5200", "200", "Clan, Name"]


# ---------------------------------------------------------------------------
# events.pyi stub: no duplicates, runtime API covered, Optional defaults
# ---------------------------------------------------------------------------

def test_events_stub_matches_runtime_and_has_no_duplicates():
    lib_dir = Path(geniuslib.__file__).parent
    stub_tree = ast.parse((lib_dir / "events.pyi").read_text(encoding="utf-8"))
    source_tree = ast.parse((lib_dir / "events.py").read_text(encoding="utf-8"))

    def classes(tree):
        return {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

    def methods(cls_node):
        return [
            node.name
            for node in cls_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

    stub_classes = classes(stub_tree)
    source_classes = classes(source_tree)

    # no redefined methods anywhere in the stub
    for name, cls_node in stub_classes.items():
        names = methods(cls_node)
        assert len(names) == len(set(names)), f"duplicate methods in stub class {name}"

    # the stub documents the event classes defined at runtime
    assert "Event" in stub_classes
    for name in ("ClanEvents", "PlayerEvents", "WarEvents", "EventsClient"):
        assert name in stub_classes, f"stub is missing class {name}"

    # every explicitly defined runtime event factory is declared in the stub
    for name in ("ClanEvents", "PlayerEvents", "WarEvents"):
        runtime_methods = {m for m in methods(source_classes[name]) if not m.startswith("_")}
        stub_methods = set(methods(stub_classes[name]))
        assert runtime_methods <= stub_methods, f"stub missing methods for {name}"

    # public EventsClient API (including login overrides) is declared
    runtime_client = {m for m in methods(source_classes["EventsClient"]) if not m.startswith("_")}
    stub_client = set(methods(stub_classes["EventsClient"]))
    assert runtime_client <= stub_client, f"stub missing: {runtime_client - stub_client}"

    # event decorator parameters are Optional with a None default at runtime
    for name in ("ClanEvents", "PlayerEvents", "WarEvents"):
        for fn in (n for n in stub_classes[name].body if isinstance(n, ast.FunctionDef)):
            for default in fn.args.defaults:
                assert isinstance(default, ast.Constant) and default.value is None
