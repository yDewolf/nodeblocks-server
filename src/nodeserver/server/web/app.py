from aiohttp import web

from nodeserver.server.protocols.policies.perm_policy_protocol import BasePermissionPolicy
from nodeserver.server.web.manager.scene_worker_manager import SceneWorkerManager
from nodeserver.server.web.manager.scene_session_manager import SceneSessionManager


class NodeServerWebApp(web.Application):
    session_manager: SceneSessionManager
    scene_worker_manager: SceneWorkerManager

    permission_policy: BasePermissionPolicy

    def setup(
        self,
        session_manager: SceneSessionManager,
        scene_worker_manager: SceneWorkerManager,
        permission_policy: BasePermissionPolicy
    ):
        self.session_manager = session_manager
        self.scene_worker_manager = scene_worker_manager
        self.permission_policy = permission_policy
