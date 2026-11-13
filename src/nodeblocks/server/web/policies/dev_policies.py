from json import JSONDecodeError

from nodeblocks.protocols.manifest.node.node_graph import SceneData
from nodeblocks.server.protocols.permission.scene_permissions import ScenePermission
from nodeblocks.server.protocols.policies.auth_policy_protocol import IAuthPolicy
from nodeblocks.server.protocols.policies.sceneperm_policy_protocol import IScenePermPolicy
from nodeblocks.server.protocols.policies.server_session_policy import IServerSessionPolicy
from nodeblocks.server.protocols.scene_list_protocol import ListedScenePerms
from nodeblocks.server.protocols.session.server_connection import ConnectionToken
from nodeblocks.server.protocols.session.session_protocols import SceneSessionToken, UserSession

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
    async def create_scene_token(self, user: UserSession, scene_id: str) -> SceneSessionToken:
        return SceneSessionToken.new(user.user_id, scene_id)

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

class DevSessionPolicy(IServerSessionPolicy):
    async def create_token(self, request: web.Request, auth_policy: IAuthPolicy) -> ConnectionToken:
        return ConnectionToken.new()

