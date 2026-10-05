from json import JSONDecodeError
from typing import Optional

from aiohttp import web
from pydantic import ValidationError
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.scene_list_protocol import ListedScene
from nodeserver.server.protocols.session_protocols import UserSession
from nodeserver.server.protocols.web.scene_messages import UpdateScenePermsModel
from nodeserver.server.web.routing.base_router import BaseRouter


class SceneHTTPRouter(BaseRouter):
    def _setup_routes(self):
        self.app.router.add_get("/api/scenes", self.get_scene_list)
        self.app.router.add_post("/api/scene/{uid}/perms", self.get_scene_perms)
        self.app.router.add_patch("/api/scene/{uid}/perms", self.update_user_perms)


    async def get_scene_list(self, request: web.Request):
        listed_scenes = self.app.scene_provider.get_listed_scenes()
        user: Optional[UserSession] = None
        try:
            user = await self.app.auth_policy.authenticate(request)
        except Exception as e:
            pass

        filtered_scenes: list[ListedScene] = []
        for scene in listed_scenes:
            if user:
                perms = await self.app.scene_perm_policy.get_scene_permissions(user, scene.uid)
            else:
                perms = await self.app.scene_perm_policy.get_default_scene_perms(scene.uid)
            
            if not ScenePermission.READ in perms:
                continue

            filtered_scenes.append(scene)


        return web.json_response({
            "scenes": [
                scene.model_dump() for scene in filtered_scenes
            ]
        })

    async def get_scene_perms(self, request: web.Request):
        scene_uid = request.match_info["uid"]

        user = await self.app.auth_policy.authenticate(request)
        perms = await self.app.scene_perm_policy.get_scene_permissions(user, scene_uid)
        return web.json_response({
            "user_perms": perms.value
        })

    async def update_user_perms(self, request: web.Request):
        scene_uid = request.match_info["uid"]
        try:
            data = await request.json()
        except JSONDecodeError as e:
            return web.json_response({"error": "invalid_json", "message": str(e)})
        try:
            parsed_data = UpdateScenePermsModel.model_validate(data)
        except ValidationError as e:
            return web.json_response({"error": "invalid_body", "message": str(e)})

        user = await self.app.auth_policy.authenticate(request)
        try:
            await self.app.scene_perm_policy.update_scene_permissions(
                user, parsed_data.target_user_id, scene_uid, parsed_data.user_perms
            )
        except Exception as e:
            return web.json_response({"error": "failed", "message": str(e)})
    
        return web.json_response()
