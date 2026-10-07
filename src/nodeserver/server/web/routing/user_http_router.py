
from aiohttp import web

from nodeserver.server.web.routing.base_router import BaseRouter


class UserHTTPRouter(BaseRouter):
    def _setup_routes(self):
        self.app.router.add_post("/api/user/login", self.handle_user_login)

    async def handle_user_login(self, request: web.Request):
        session = await self.app.auth_policy.authenticate(request)
        # TODO: talvez enviar um token de autenticação ou algo do tipo
        return web.json_response({
            "user_id": session.user_id,
            "display_name": session.display_name
        })
