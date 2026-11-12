import logging

from aiohttp import web

from nodeblocks.server.server_env import SERVER_ENV
from nodeblocks.server.web.routing.base_router import BaseRouter

logger = logging.getLogger("nds.server")

class RemoteHTTPRouter(BaseRouter):
    def _setup_routes(self):
        self.app.router.add_get("/api/health-check", self.health_check)
        if SERVER_ENV.include_remote_access_routes:
            logger.warning("Including remote access routes. Beware that this is experimental and should be used only in local environments.")

    async def health_check(self, request: web.Request):
        return web.json_response()
