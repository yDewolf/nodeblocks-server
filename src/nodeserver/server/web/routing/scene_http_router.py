from json import JSONDecodeError

from aiohttp import web
from pydantic import ValidationError
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.web.scene_messages import GetScenePermsModel, UpdateScenePermsModel
from nodeserver.server.web.routing.base_router import BaseRouter


class SceneHTTPRouter(BaseRouter):
    def _setup_routes(self):
        self.app.router.add_get("/api/scenes", self.get_scene_list)
        self.app.router.add_post("/api/scene/{uid}/perms", self.get_scene_perms)
        self.app.router.add_patch("/api/scene/{uid}/perms", self.update_user_perms)


    async def get_scene_list(self, request: web.Request):
        listed_scenes = self.app.scene_provider.get_listed_scenes()
        return web.json_response({
            "scenes": [
                scene.model_dump() for scene in listed_scenes
            ]
        })

    async def get_scene_perms(self, request: web.Request):
        scene_uid = request.match_info["uid"]
        try:
            data = await request.json()
        except JSONDecodeError as e:
            return web.json_response({"error": "invalid_json", "message": str(e)})
        try:
            parsed_data = GetScenePermsModel.model_validate(data)
        except ValidationError as e:
            return web.json_response({"error": "invalid_body", "message": str(e)})

        perms = self.app.scene_provider.get_scene_permissions(scene_uid, parsed_data.user_id)
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

        actor_perms = self.app.scene_provider.get_scene_permissions(
            scene_uid, parsed_data.user_id
        )

        if not ScenePermission.ADMIN in actor_perms:
            return web.HTTPUnauthorized(reason="User must have admin permissions to update another user's permission")

        self.app.scene_provider.update_scene_permissions(
            scene_uid, parsed_data.target_user_id, parsed_data.user_perms
        )
        return web.HTTPAccepted()
