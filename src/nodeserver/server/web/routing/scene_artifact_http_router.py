from typing import Optional

from aiohttp import web
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.session_protocols import UserSession
from nodeserver.server.web.routing.base_router import BaseRouter


class SceneArtifactHTTPRouter(BaseRouter):
    def _setup_routes(self):
        self.app.router.add_post(
            "/api/scene/{uid}/artifacts/{node_uid}/{filename}", 
            self.get_node_artifact
        )
        self.app.router.add_get(
            "/api/scene/{uid}/artifacts/{node_uid}/{filename}", 
            self.get_node_artifact
        )

    async def get_node_artifact(self, request: web.Request):
        scene_uid = request.match_info["uid"]
        node_uid = request.match_info["node_uid"]
        filename = request.match_info["filename"]

        user: Optional[UserSession] = None
        try:
            user = await self.app.auth_policy.authenticate(request)
        except Exception:
            pass

        if user:
            perms = await self.app.scene_perm_policy.get_scene_permissions(user, scene_uid)
        else:
            perms = await self.app.scene_perm_policy.get_default_scene_perms(scene_uid)
        
        if ScenePermission.READ not in perms:
            return web.HTTPUnauthorized()

        try:
            artifact_provider = self.app.scene_artifact_provider
            file_path = artifact_provider.get_secure_artifact_path(scene_uid, node_uid, filename)
        except Exception as e:
            return web.json_response(
                {"error": "failed", "message": f"Failed to process artifact path: {str(e)}"}, 
                status=500
            )

        if not file_path or not file_path.exists() or not file_path.is_file():
            return web.HTTPNotFound()

        return web.FileResponse(file_path)
