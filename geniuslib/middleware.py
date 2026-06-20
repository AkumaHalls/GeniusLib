"""Middleware/Pipeline system for GeniusLib.

Allows intercepting and transforming HTTP requests and responses
via a chain of middleware functions, similar to frameworks like
FastAPI, Django, or Starlette.

Usage::

    from geniuslib.middleware import Middleware, middleware

    @middleware('request')
    async def log_request(request):
        print(f"Request: {request.method} {request.url}")

    @middleware('response')
    async def log_response(response):
        print(f"Response: {response.status}")

    client = Client()
    client.http.add_middleware(log_request, log_response)
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, List, Optional

LOG = logging.getLogger(__name__)


@dataclass
class Request:
    """Represents an HTTP request being intercepted by middleware.

    Attributes
    ----------
    method : str
        HTTP method (GET, POST, etc.).
    url : str
        The full request URL.
    headers : dict
        Request headers.
    kwargs : dict
        Additional arguments passed to the HTTP request.
    """
    method: str
    url: str
    headers: dict = field(default_factory=dict)
    kwargs: dict = field(default_factory=dict)


@dataclass
class Response:
    """Represents an HTTP response being intercepted by middleware.

    Attributes
    ----------
    status : int
        HTTP status code.
    data : Any
        The response data (parsed JSON or text).
    headers : dict
        Response headers.
    elapsed_ms : float
        Time elapsed for the request in milliseconds.
    """
    status: int
    data: Any = None
    headers: dict = field(default_factory=dict)
    elapsed_ms: float = 0.0


RequestMiddleware = Callable[[Request], Awaitable[Optional[Request]]]
ResponseMiddleware = Callable[[Response], Awaitable[Optional[Response]]]


class Middleware:
    """Holds a chain of request and response middleware functions.

    Request middlewares receive a :class:`Request` and may return
    ``None`` to abort the request, or a modified :class:`Request`
    to continue the chain.

    Response middlewares receive a :class:`Response` and may return
    ``None`` to abort processing, or a modified :class:`Response`
    to continue.
    """

    __slots__ = ("_request_chain", "_response_chain")

    def __init__(self):
        self._request_chain: List[RequestMiddleware] = []
        self._response_chain: List[ResponseMiddleware] = []

    def add_request(self, func: RequestMiddleware) -> RequestMiddleware:
        """Register a request middleware function."""
        self._request_chain.append(func)
        return func

    def add_response(self, func: ResponseMiddleware) -> ResponseMiddleware:
        """Register a response middleware function."""
        self._response_chain.append(func)
        return func

    def remove_request(self, func: RequestMiddleware) -> None:
        """Remove a previously registered request middleware."""
        try:
            self._request_chain.remove(func)
        except ValueError:
            pass

    def remove_response(self, func: ResponseMiddleware) -> None:
        """Remove a previously registered response middleware."""
        try:
            self._response_chain.remove(func)
        except ValueError:
            pass

    async def run_request(self, req: Request) -> Optional[Request]:
        """Run the request through all registered request middlewares."""
        for mw in self._request_chain:
            try:
                result = await mw(req)
            except Exception as e:
                LOG.error("Request middleware %s raised %s", mw.__name__, e)
                raise
            if result is None:
                return None
            req = result
        return req

    async def run_response(self, resp: Response) -> Optional[Response]:
        """Run the response through all registered response middlewares."""
        for mw in self._response_chain:
            try:
                result = await mw(resp)
            except Exception as e:
                LOG.error("Response middleware %s raised %s", mw.__name__, e)
                raise
            if result is None:
                return None
            resp = result
        return resp

    def clear(self) -> None:
        """Remove all registered middlewares."""
        self._request_chain.clear()
        self._response_chain.clear()


def middleware(event_type: str = "request"):
    """Decorator to create a middleware function.

    Parameters
    ----------
    event_type : str
        Either ``"request"`` or ``"response"``.

    Usage::

        @middleware('request')
        async def my_middleware(request):
            print(request.url)
            return request
    """
    if event_type not in ("request", "response"):
        raise ValueError("event_type must be 'request' or 'response'")

    def decorator(func):
        func._middleware_type = event_type
        return func

    return decorator


# --- Built-in middlewares ---

@middleware("request")
async def request_logger(req: Request) -> Request:
    """Log outgoing requests at DEBUG level."""
    LOG.debug(">>> %s %s", req.method, req.url)
    return req


@middleware("response")
async def response_logger(resp: Response) -> Response:
    """Log incoming responses at DEBUG level."""
    LOG.debug("<<< %s (%d, %.1fms)", resp.status, resp.status, resp.elapsed_ms)
    return resp


@middleware("request")
async def timing_header(req: Request) -> Request:
    """Inject a timestamp into the request for latency tracking."""
    req.kwargs["_geniuslib_start"] = time.monotonic()
    return req
