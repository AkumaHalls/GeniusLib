"""Tests for the middleware module."""

import pytest
from unittest.mock import AsyncMock
from unittest.mock import MagicMock, AsyncMock
from itertools import cycle
from geniuslib.http import HTTPClient, Route
from geniuslib.middleware import (
    Middleware, Request, Response,
    middleware, request_logger, response_logger,
)


class TestMiddleware:
    @pytest.mark.asyncio
    async def test_request_middleware(self):
        mw = Middleware()
        calls = []

        @middleware("request")
        async def add_header(req):
            calls.append("request")
            req.headers["X-Test"] = "true"
            return req

        mw.add_request(add_header)
        req = Request(method="GET", url="http://test.com")
        result = await mw.run_request(req)

        assert result is not None
        assert result.headers["X-Test"] == "true"
        assert calls == ["request"]

    @pytest.mark.asyncio
    async def test_response_middleware(self):
        mw = Middleware()
        calls = []

        @middleware("response")
        async def modify_data(resp):
            calls.append("response")
            resp.data = {"modified": True}
            return resp

        mw.add_response(modify_data)
        resp = Response(status=200, data={"original": True})
        result = await mw.run_response(resp)

        assert result is not None
        assert result.data["modified"] is True
        assert calls == ["response"]

    @pytest.mark.asyncio
    async def test_request_abort(self):
        mw = Middleware()

        @middleware("request")
        async def abort(req):
            return None

        mw.add_request(abort)
        req = Request(method="GET", url="http://test.com")
        result = await mw.run_request(req)
        assert result is None

    @pytest.mark.asyncio
    async def test_response_abort(self):
        mw = Middleware()

        @middleware("response")
        async def abort(resp):
            return None

        mw.add_response(abort)
        resp = Response(status=200)
        result = await mw.run_response(resp)
        assert result is None

    @pytest.mark.asyncio
    async def test_multiple_middlewares_chain(self):
        mw = Middleware()
        order = []

        @middleware("request")
        async def mw1(req):
            order.append("mw1")
            return req

        @middleware("request")
        async def mw2(req):
            order.append("mw2")
            return req

        mw.add_request(mw1)
        mw.add_request(mw2)
        await mw.run_request(Request(method="GET", url="http://test.com"))

        assert order == ["mw1", "mw2"]

    @pytest.mark.asyncio
    async def test_remove_middleware(self):
        mw = Middleware()

        @middleware("request")
        async def my_mw(req):
            return req

        mw.add_request(my_mw)
        assert len(mw._request_chain) == 1

        mw.remove_request(my_mw)
        assert len(mw._request_chain) == 0

    def test_clear(self):
        mw = Middleware()

        @middleware("request")
        async def r1(req):
            return req

        @middleware("response")
        async def r2(resp):
            return resp

        mw.add_request(r1)
        mw.add_response(r2)
        mw.clear()

        assert len(mw._request_chain) == 0
        assert len(mw._response_chain) == 0

    def test_invalid_event_type(self):
        with pytest.raises(ValueError, match="event_type must be"):
            @middleware("invalid")
            async def bad_mw(req):
                return req

    def test_builtin_loggers(self):
        assert request_logger._middleware_type == "request"
        assert response_logger._middleware_type == "response"

    @pytest.mark.asyncio
    async def test_add_middleware_to_client(self):
        from geniuslib.http import HTTPClient

        client = MagicMock()
        loop = MagicMock()
        http = HTTPClient(
            client=client,
            loop=loop,
            email="test@test.com",
            password="test",
            key_names="test",
            key_count=1,
            key_scopes="clash",
            throttle_limit=30,
            base_url="https://api.clashofclans.com/v1",
        )

        @middleware("request")
        async def test_mw(req):
            return req

        http.add_middleware(test_mw)
        assert len(http.middleware._request_chain) == 1

        http.remove_middleware(test_mw)
        assert len(http.middleware._request_chain) == 0

    @pytest.mark.asyncio
    async def test_middleware_integration_with_request(self):
        from unittest.mock import MagicMock, AsyncMock, patch

        @middleware("request")
        async def custom_req_mw(req):
            req.headers["X-Custom"] = "true"
            return req

        @middleware("response")
        async def custom_resp_mw(resp):
            resp.data["processed"] = True
            return resp

        client = MagicMock()
        loop = MagicMock()
        http = HTTPClient(
            client=client,
            loop=loop,
            email="test@test.com",
            password="test",
            key_names="test",
            key_count=1,
            key_scopes="clash",
            throttle_limit=30,
            cache_max_size=0,
            base_url="https://api.clashofclans.com/v1",
        )

        http.initialising_keys.set()
        http.add_middleware(custom_req_mw, custom_resp_mw)
        http._keys = ["test_key"]
        http.keys = cycle(http._keys)
        mock_session = AsyncMock()
        http._HTTPClient__session = mock_session

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json = AsyncMock(return_value={"name": "TestClan"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        route = Route("GET", "https://api.clashofclans.com/v1", "/clans/%23TEST")

        result = await http.request(route)

        assert result["processed"] is True
        assert result["name"] == "TestClan"


