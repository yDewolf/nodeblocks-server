from aiohttp import web

from nodeblocks.server.protocols.session.server_connection import ConnectionToken
from nodeblocks.server.web.app import NodeServerWebApp
from nodeblocks.server.web.middlewares.base_middlewares import MiddlewareHandler

@web.middleware
async def token_auth_middleware(
    request: web.Request,
    handler: MiddlewareHandler
) -> web.StreamResponse:
    if not isinstance(request.app, NodeServerWebApp): return web.HTTPInternalServerError()
    if request.method.lower() == "options":
        return await handler(request)
    
    if request.path in request.app.public_routes:
        return await handler(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return web.json_response({"error": "unauthorized", "message": "Missing or invalid token header"}, status=401)

    token_str = auth_header.split(" ")[1]

    try:
        token_payload = ConnectionToken.from_token_str(token_str)
        request["token_payload"] = token_payload
    
    except Exception as e:
        return web.json_response({"error": "unauthorized", "message": f"Invalid token: {str(e)}"}, status=401)

    return await handler(request)

