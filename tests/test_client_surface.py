"""Surface regression tests for :class:`geniuslib.client.Client`.

These cover the client-side audit items only: lazy event-loop resolution,
unknown constructor keyword arguments, per-client ``LoadGameData``, login
failure cleanup, ``_defaults`` routing in ``get_player`` and defensive
payload handling. No test performs network I/O.
"""

import asyncio
import gc
import logging
import warnings
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from geniuslib.client import Client
from geniuslib.errors import InvalidCredentials
from geniuslib.http import HTTPClient, Route
from geniuslib.miscmodels import LoadGameData
from geniuslib.players import Player


class _Captured(Exception):
    """Sentinel raised by the recording model constructor."""


def test_construction_never_touches_the_event_loop(monkeypatch):
    touched = []
    real_new_event_loop = asyncio.new_event_loop
    real_get_event_loop = asyncio.get_event_loop

    def spy_new_event_loop(*args, **kwargs):
        touched.append("new_event_loop")
        return real_new_event_loop(*args, **kwargs)

    def spy_get_event_loop(*args, **kwargs):
        touched.append("get_event_loop")
        return real_get_event_loop(*args, **kwargs)

    monkeypatch.setattr(asyncio, "new_event_loop", spy_new_event_loop)
    monkeypatch.setattr(asyncio, "get_event_loop", spy_get_event_loop)

    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        client = Client(key_count=1)
        gc.collect()

    assert touched == []
    assert not [w for w in recorded if issubclass(w.category, ResourceWarning)]
    assert client.load_game_data.default is True


async def test_loop_property_prefers_the_running_loop():
    client = Client(key_count=1)
    assert client.loop is asyncio.get_running_loop()

    stale = asyncio.new_event_loop()
    try:
        client.loop = stale
        assert client.loop is asyncio.get_running_loop()
    finally:
        stale.close()


def test_loop_property_uses_the_stored_loop_outside_a_loop():
    loop = asyncio.new_event_loop()
    other = asyncio.new_event_loop()
    try:
        client = Client(key_count=1, loop=loop)
        assert client.loop is loop

        client.loop = other
        assert client.loop is other
    finally:
        loop.close()
        other.close()


def test_loop_property_resolves_and_caches_lazily(monkeypatch):
    created = []
    real_new_event_loop = asyncio.new_event_loop

    def spy_new_event_loop(*args, **kwargs):
        loop = real_new_event_loop(*args, **kwargs)
        created.append(loop)
        return loop

    monkeypatch.setattr(asyncio, "new_event_loop", spy_new_event_loop)

    client = Client(key_count=1)
    try:
        resolved = client.loop
        assert not resolved.is_closed()
        assert client.loop is resolved
        assert len(created) <= 1
    finally:
        for loop in created:
            loop.close()


def test_unknown_client_kwargs_are_logged(caplog):
    with caplog.at_level(logging.WARNING, logger="geniuslib.client"):
        Client(key_count=1, bogus_option=True, another_typo="x")

    assert "bogus_option" in caplog.text
    assert "another_typo" in caplog.text
    assert "check for typos" in caplog.text


def test_events_client_reserved_options_are_not_reported(caplog):
    with caplog.at_level(logging.WARNING, logger="geniuslib.client"):
        Client(
            key_count=1,
            cwl_active=True,
            check_cwl_prep=True,
            raid_clan_tag="#CLAN",
            maintenance_player_tag="#PLAYER",
        )

    assert "Ignoring unexpected Client keyword arguments" not in caplog.text
    assert "cwl_active" not in caplog.text


def test_load_game_data_is_not_shared_between_clients():
    first = Client(key_count=1)
    second = Client(key_count=1)

    assert first.load_game_data is not second.load_game_data
    assert first.load_game_data.default is True
    assert second.load_game_data.default is True

    first.load_game_data.always = True
    assert second.load_game_data.always is False

    explicit = LoadGameData(startup_only=True)
    third = Client(key_count=1, load_game_data=explicit)
    assert third.load_game_data is explicit
    assert third.load_game_data.startup_only is True


async def test_login_failure_closes_session_and_propagates(monkeypatch):
    async def boom(self):
        raise InvalidCredentials("developer site rejected the login")

    monkeypatch.setattr(HTTPClient, "initialise_keys", boom)

    closed = []
    real_close = HTTPClient.close

    async def spy_close(self):
        closed.append(True)
        return await real_close(self)

    monkeypatch.setattr(HTTPClient, "close", spy_close)

    client = Client(key_count=1)
    with pytest.raises(InvalidCredentials):
        await client.login("user@example.com", "secret")

    http = client.http
    assert http is not None
    assert http._HTTPClient__session is None
    assert http.keys is None
    assert closed == [True]

    with pytest.raises(InvalidCredentials):
        await http.request(Route("GET", client.base_url, "/players/%23XYZ"))

    await client.close()
    assert closed == [True, True]
    await client.close()
    assert closed == [True, True, True]


async def test_login_with_tokens_session_failure_propagates_and_closes(monkeypatch):
    async def boom(self, connector, timeout):
        raise RuntimeError("session could not be created")

    monkeypatch.setattr(HTTPClient, "create_session", boom)

    closed = []
    real_close = HTTPClient.close

    async def spy_close(self):
        closed.append(True)
        return await real_close(self)

    monkeypatch.setattr(HTTPClient, "close", spy_close)

    client = Client(key_count=1)
    with pytest.raises(RuntimeError):
        await client.login_with_tokens("TOKEN")

    assert client.http is not None
    assert closed == [True]

    await client.close()


async def test_get_player_forwards_defaults_to_http_and_kwargs_to_model():
    http_calls = {}
    model_calls = {}

    async def fake_get_player(player_tag, **kwargs):
        http_calls["player_tag"] = player_tag
        http_calls.update(kwargs)
        return {"tag": player_tag}

    class RecordingPlayer(Player):
        def __init__(self, **kwargs):
            model_calls.update(kwargs)
            raise _Captured()

    client = Client(key_count=1)
    client.http = SimpleNamespace(get_player=fake_get_player)

    with pytest.raises(_Captured):
        await client.get_player(
            "#ABC123",
            cls=RecordingPlayer,
            members={"leader": "#OTHER"},
            lookup_cache=False,
        )

    assert http_calls == {
        "player_tag": "#ABC123",
        "lookup_cache": False,
        "update_cache": True,
        "ignore_cached_errors": None,
        "realtime": False,
    }
    assert model_calls.get("members") == {"leader": "#OTHER"}
    assert "realtime" not in model_calls
    assert "update_cache" not in model_calls
    assert "ignore_cached_errors" not in model_calls


async def test_search_locations_tolerates_missing_items():
    async def fake_search_locations(**kwargs):
        return {}

    client = Client(key_count=1)
    client.http = SimpleNamespace(search_locations=fake_search_locations)

    assert await client.search_locations() == []


async def test_verify_player_token_tolerates_partial_payload():
    responses = iter([{}, {"status": "ok"}, {"status": "failed"}])

    async def fake_verify_player_token(player_tag, token, **kwargs):
        return next(responses)

    client = Client(key_count=1)
    client.http = SimpleNamespace(verify_player_token=fake_verify_player_token)

    assert await client.verify_player_token("#ABC123", "token") is False
    assert await client.verify_player_token("#ABC123", "token") is True
    assert await client.verify_player_token("#ABC123", "token") is False


async def test_close_is_idempotent_and_safe_before_login():
    client = Client(key_count=1)
    await client.close()

    spy = AsyncMock()
    client.http = SimpleNamespace(close=spy)
    await client.close()
    await client.close()
    assert spy.await_count == 2

    other = Client(key_count=1)
    other.http = SimpleNamespace(close=spy)
    async with other:
        pass
    assert spy.await_count == 3


async def test_dispatch_schedules_listener_on_the_running_loop():
    class _ListenerClient(Client):
        __slots__ = ("fired",)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.fired = asyncio.Event()

        async def ping(self):
            self.fired.set()

    client = _ListenerClient(key_count=1)
    client.dispatch("ping")
    await asyncio.wait_for(client.fired.wait(), timeout=1)
