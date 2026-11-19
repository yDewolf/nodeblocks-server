from aiohttp import web

from nodeblocks.server.web.app import NodeServerWebApp
from nodeblocks.server.web.manager.server_status_manager import ServerStatusManager
from nodeblocks.server.web.middlewares.base_middlewares import MiddlewareHandler


@web.middleware
async def ready_gate_middleware(
    request: web.Request,
    handler: MiddlewareHandler
) -> web.StreamResponse:
    if not isinstance(request.app, NodeServerWebApp): return web.HTTPInternalServerError()
    if request.method.lower() == "options":
        return await handler(request)

    if request.path in request.app.ready_bypass:
        return await handler(request)

    is_ready = await request.app.server_status_manager.wait_until_ready(timeout=30.0)
    if not is_ready:
        return web.json_response(
            {"error": "Timeout", "message": "Server took too long to init."},
            status=503,
        )

    return await handler(request)
