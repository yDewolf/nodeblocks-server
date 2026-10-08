from typing import Any

from aiohttp import web

from nodeserver.protocols.manifest.node.node_graph import SceneData
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.policies.sceneperm_policy_protocol import IScenePermPolicy
from nodeserver.server.protocols.session_protocols import UserSession
from nodeserver.server.web.policies.base_policy import BaseWebPolicy


class FilePermissionPolicy(BaseWebPolicy, IScenePermPolicy):
    async def get_default_scene_perms(self, scene_id: str) -> ScenePermission:
        return self.app.scene_provider.get_default_scene_perms(scene_id)

    async def get_scene_permissions(self, user: UserSession, scene_id: str) -> ScenePermission:
        return self.app.scene_provider.get_scene_permissions(
            scene_id, user.user_id
        )

    async def update_scene_permissions(self, user: UserSession, target_user: str, scene_id: str, perms: ScenePermission):
        actor_perms = self.app.scene_provider.get_scene_permissions(
            scene_id, user.user_id
        )

        if not ScenePermission.ADMIN in actor_perms:
            # TODO: better exceptions I guess
            raise Exception("User must have admin permissions to update another user's permission")

        self.app.scene_provider.update_scene_permissions(
            scene_id, target_user, perms
        )

    async def get_scene_data(self, user: UserSession, scene_id: str) -> SceneData:
        perms = self.app.scene_provider.get_scene_permissions(scene_id, user.user_id)
        if not ScenePermission.VIEWER in perms:
            # TODO: better exceptions I guess
            raise Exception("User must have view permission to get scene data")
        
        scene_data = self.app.scene_provider.load_scene_data(scene_id)
        if not scene_data:
            # TODO: better exceptions I guess
            raise Exception(f"Couldn't find scene data for scene: {scene_id}")

        return scene_data