from pathlib import Path
from aiohttp import web

from nodeserver.engine.helpers.plugin_subprocess_helper import PluginSubprocessHelper
from nodeserver.engine.plugins.plugin_spec_manager import PluginSpecManager
from nodeserver.server.protocols.policies.perm_policy_protocol import BasePermissionPolicy
from nodeserver.server.web.manager.scene_worker_manager import SceneWorkerManager
from nodeserver.server.web.manager.scene_session_manager import SceneSessionManager


class NodeServerWebApp(web.Application):
    plugin_manager: PluginSpecManager
    session_manager: SceneSessionManager
    scene_worker_manager: SceneWorkerManager

    permission_policy: BasePermissionPolicy

    def _setup(
        self,
        plugin_manager: PluginSpecManager,
        session_manager: SceneSessionManager,
        scene_worker_manager: SceneWorkerManager,
        permission_policy: BasePermissionPolicy
    ):
        self.plugin_manager = plugin_manager
        self.session_manager = session_manager
        self.scene_worker_manager = scene_worker_manager
        self.permission_policy = permission_policy

    def _setup_plugins(self, plugins_folder: Path):
        PluginSubprocessHelper.setup_and_load_plugins(plugins_folder, self.plugin_manager)
