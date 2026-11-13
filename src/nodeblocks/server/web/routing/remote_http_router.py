import asyncio
import logging

from aiohttp import web

from nodeblocks.server.protocols.session.server_connection import ConnectionToken, ServerConnectionSession
from nodeblocks.server.server_env import SERVER_ENV
from nodeblocks.server.web.routing.base_router import BaseRouter

logger = logging.getLogger("nds.server")

class RemoteHTTPRouter(BaseRouter):
    def _setup_routes(self):
        self.app.router.add_get("/api/health-check", self.health_check)
        self.app.router.add_get("/api/server/token", self.create_connection_token)
        self.app.router.add_get("/api/server/events", self.server_events_handler)

        if SERVER_ENV.include_remote_access_routes:
            logger.warning("Including remote access routes. Beware that this is experimental and should be used only in local environments.")

    async def health_check(self, request: web.Request):
        return web.json_response()


    async def create_connection_token(self, request: web.Request):
        try:
            token = await self.app.session_policy.create_token(request, self.app.auth_policy)
        except Exception as e:
            return web.json_response({"error": "Failed to create token", "message": str(e)})

        return web.json_response(str(token))


    async def server_events_handler(self, request: web.Request):
        token_str = request.query.get("token")
        if not token_str:
            return web.json_response({"error": "Bad payload", "message": "Missing connection token"}, status=401)
        
        try:
            token_payload = ConnectionToken.from_token_str(token_str)
        except Exception as e:
            return web.json_response({"error": "Invalid token", "message": str(e)}, status=401)

        response = web.StreamResponse()
        response.content_type = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'

        await response.prepare(request)
        session = ServerConnectionSession(socket=response, token_payload=token_payload)
        
        self.app.server_session_manager.register_connection(session)
        await self.app.server_status_manager.send_current_status(session.id)

        try:
            while True:
                await asyncio.sleep(SERVER_ENV.server_event_ping_interval)
                await response.write(b":ping\n\n")
        
        except (asyncio.CancelledError, ConnectionResetError):
            logger.info("Client disconnected from server events: %s", session.id)
        finally:
            self.app.server_session_manager.unregister_connection(session.id)

        return response
