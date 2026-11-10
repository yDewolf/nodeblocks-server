from typing import Any

from aiohttp import web

from nodeblocks.protocols.manifest.node.node_graph import SceneData
from nodeblocks.server.protocols.permission.scene_permissions import ScenePermission
from nodeblocks.server.protocols.policies.sceneperm_policy_protocol import IScenePermPolicy
from nodeblocks.server.protocols.scene_list_protocol import ListedScenePerms
from nodeblocks.server.protocols.session_protocols import SceneSessionToken, UserSession
from nodeblocks.server.web.exceptions.scene_perm_exceptions import SceneNotFoundError, SceneUnauthorizedActionError
from nodeblocks.server.web.policies.base_policy import BaseWebPolicy


class FilePermissionPolicy(BaseWebPolicy, IScenePermPolicy):
    async def create_scene_token(self, user: UserSession, scene_id: str) -> SceneSessionToken:
        perms = self.app.scene_provider.get_scene_permissions(scene_id, user.user_id)
        if not ScenePermission.VIEWER in perms:
            raise SceneUnauthorizedActionError(self.__class__, "create_scene_token", user.user_id, perms, ScenePermission.VIEWER)
        
        return SceneSessionToken.new(user.user_id, scene_id)
    
    async def get_default_scene_perms(self, scene_id: str) -> ScenePermission:
        return self.app.scene_provider.get_default_scene_perms(scene_id)

    async def get_scene_permissions(self, user: UserSession, scene_id: str) -> ScenePermission:
        return self.app.scene_provider.get_scene_permissions(
            scene_id, user.user_id
        )

    async def get_all_scene_perms(self, user: UserSession, scene_id: str) -> ListedScenePerms:
        actor_perms = self.app.scene_provider.get_scene_permissions(
            scene_id, user.user_id
        )

        if not ScenePermission.ADMIN in actor_perms:
            raise SceneUnauthorizedActionError(self.__class__, "get_all_scene_perms", user.user_id, actor_perms, ScenePermission.ADMIN)

        perms = self.app.scene_provider.get_all_scene_perms(scene_id)
        return perms

    async def update_scene_permissions(self, user: UserSession, target_user: str, scene_id: str, perms: ScenePermission):
        actor_perms = self.app.scene_provider.get_scene_permissions(
            scene_id, user.user_id
        )

        if not ScenePermission.ADMIN in actor_perms:
            raise SceneUnauthorizedActionError(self.__class__, "update_scene_permissions", user.user_id, actor_perms, ScenePermission.ADMIN)

        self.app.scene_provider.update_scene_permissions(
            scene_id, perms, user_id=target_user
        )

    async def update_default_scene_perms(self, user: UserSession, scene_id: str, perms: ScenePermission):
        actor_perms = self.app.scene_provider.get_scene_permissions(
            scene_id, user.user_id
        )

        if not ScenePermission.ADMIN in actor_perms:
            raise SceneUnauthorizedActionError(self.__class__, "update_default_scene_perms", user.user_id, actor_perms, ScenePermission.ADMIN)

        self.app.scene_provider.update_scene_permissions(
            scene_id, perms
        )

    async def get_scene_data(self, user: UserSession, scene_id: str) -> SceneData:
        perms = self.app.scene_provider.get_scene_permissions(scene_id, user.user_id)
        if not ScenePermission.VIEWER in perms:
            raise SceneUnauthorizedActionError(self.__class__, "get_scene_data", user.user_id, perms, ScenePermission.VIEWER)
        
        scene_data = self.app.scene_provider.load_scene_data(scene_id)
        if not scene_data:
            raise SceneNotFoundError(self.__class__, scene_id)

        return scene_data
