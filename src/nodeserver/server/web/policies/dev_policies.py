from json import JSONDecodeError

from nodeserver.protocols.manifest.node.node_graph import SceneData
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.policies.auth_policy_protocol import IAuthPolicy
from nodeserver.server.protocols.policies.sceneperm_policy_protocol import IScenePermPolicy
from nodeserver.server.protocols.scene_list_protocol import ListedScenePerms
from nodeserver.server.protocols.session_protocols import UserSession

from aiohttp import web

class DevAuthPolicy(IAuthPolicy):
    async def authenticate(self, request: web.Request) -> UserSession:
        try:
            data = await request.json()
        except JSONDecodeError as e:
            raise Exception("Failed to authenticate: invalid body")

        user_id = dict(data).get("user_id") or "dev_user"
        return UserSession(user_id=user_id, display_name=f"User-{user_id}")

class DevScenePermPolicy(IScenePermPolicy):
    async def get_scene_permissions(self, user: UserSession, scene_id: str) -> ScenePermission:
        return ScenePermission.ALL


    async def get_default_scene_perms(self, scene_id: str) -> ScenePermission:
        return ScenePermission.ALL

    async def get_all_scene_perms(self, user: UserSession, scene_id: str) -> ListedScenePerms:
        return await super().get_all_scene_perms(user, scene_id)

    async def get_scene_data(self, user: UserSession, scene_id: str) -> SceneData:
        return await super().get_scene_data(user, scene_id)

    async def update_scene_permissions(self, user: UserSession, target_user: str, scene_id: str, perms: ScenePermission):
        pass

    async def update_default_scene_perms(self, user: UserSession, scene_id: str, perms: ScenePermission):
        pass
