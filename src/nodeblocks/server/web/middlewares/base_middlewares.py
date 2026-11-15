from typing import Awaitable, Callable

from aiohttp import web

MiddlewareHandler = Callable[[web.Request], Awaitable[web.StreamResponse]]
