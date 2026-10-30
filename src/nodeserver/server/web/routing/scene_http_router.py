from json import JSONDecodeError
from typing import Optional

from aiohttp import web
from pydantic import ValidationError
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.scene_list_protocol import ListedScene
from nodeserver.server.protocols.session_protocols import SceneSessionToken, UserSession
from nodeserver.server.protocols.web.scene_requests import CreateSceneModel, UpdateScenePermsModel
from nodeserver.server.web.routing.base_router import BaseRouter


class SceneHTTPRouter(BaseRouter):
    def _setup_routes(self):
        self.app.router.add_get("/api/scenes", self.get_scene_list)
        self.app.router.add_post("/api/scenes", self.get_scene_list)
        self.app.router.add_post("/api/scene/create", self.create_scene)

        self.app.router.add_post("/api/scene/{uid}", self.get_scene_data)
        self.app.router.add_post("/api/scene/{uid}/token", self.handle_scene_token_create)
        self.app.router.add_post("/api/scene/{uid}/perms", self.get_scene_perms)

        # Use ?targetUser=... to update a user's permission. 
        # Otherwise it will update default scene permissions
        self.app.router.add_patch("/api/scene/{uid}/perms", self.update_scene_perms)


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

            scene.user_perms = perms
            filtered_scenes.append(scene)


        return web.json_response([
            scene.model_dump(mode="json") for scene in filtered_scenes
        ])

    async def get_scene_data(self, request: web.Request):
        scene_uid = request.match_info["uid"]
        user = await self.app.auth_policy.authenticate(request)
        try:
            data = await self.app.scene_perm_policy.get_scene_data(user, scene_uid)

        except Exception as e:
            return web.json_response({"error": "failed", "message": str(e)})
        
        return web.json_response(data.model_dump())

    async def get_scene_perms(self, request: web.Request):
        scene_uid = request.match_info["uid"]
        user = await self.app.auth_policy.authenticate(request)
        
        target = request.query.get("target")
        if target == "all":
            listed_perms = await self.app.scene_perm_policy.get_all_scene_perms(user, scene_uid)
            return web.json_response(
                listed_perms.model_dump(mode="json")
            )

        perms = await self.app.scene_perm_policy.get_scene_permissions(user, scene_uid)
        return web.json_response({
            "user_perms": perms.value
        })

    async def update_scene_perms(self, request: web.Request):
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
        target_user = request.query.get("targetUser")
        try:
            if target_user:
                await self.app.scene_perm_policy.update_scene_permissions(
                    user, target_user, scene_uid, parsed_data.user_perms
                )
            else:
                await self.app.scene_perm_policy.update_default_scene_perms(
                    user, scene_uid, parsed_data.user_perms
                )
        except Exception as e:
            return web.json_response({"error": "failed", "message": str(e)})
    
        return web.HTTPSuccessful()

    async def handle_scene_token_create(self, request: web.Request):
        try:
            data = await request.json()
        except JSONDecodeError as e:
            return web.json_response({"error": "invalid_json", "message": str(e)})

        user = await self.app.auth_policy.authenticate(request)

        scene_id = request.match_info["uid"]
        token = SceneSessionToken.new(user.user_id, scene_id)
        return web.json_response({
            "token": str(token),
            "scene_id": scene_id
        })


    async def create_scene(self, request: web.Request):
        try:
            data = await request.json()
        except JSONDecodeError as e:
            return web.json_response({"error": "invalid_json", "message": str(e)})

        user = await self.app.auth_policy.authenticate(request)

        try:
            parsed_data = CreateSceneModel.model_validate(data)
        except ValidationError as e:
            return web.json_response({"error": "invalid_body", "message": str(e)})
        
        try:
            self.app.scene_provider.create_scene(parsed_data.scene_id, user.user_id, parsed_data.default_perm)
        except Exception as e:
            return web.json_response({"error": "failed", "message": str(e)})

        return web.HTTPSuccessful()

