from pathlib import Path
from aiohttp import web

from nodeserver.engine.helpers.plugin_subprocess_helper import PluginSubprocessHelper
from nodeserver.engine.plugins.plugin_spec_manager import PluginSpecManager
from nodeserver.server.protocols.policies.auth_policy_protocol import IAuthPolicy
from nodeserver.server.protocols.policies.sceneperm_policy_protocol import IScenePermPolicy
from nodeserver.server.protocols.providers.metadata_provider_protocol import IMetadataProvider, IServerMetadataProvider
from nodeserver.server.protocols.providers.scene_provider_protocol import IServerSceneProvider
from nodeserver.server.web.manager.scene_worker_manager import SceneWorkerManager
from nodeserver.server.web.manager.scene_session_manager import SceneSessionManager


class NodeServerWebApp(web.Application):
    # TODO: separar algumas coisas aqui em módulos diferentes
    plugin_manager: PluginSpecManager
    session_manager: SceneSessionManager
    scene_worker_manager: SceneWorkerManager

    auth_policy: IAuthPolicy
    scene_perm_policy: IScenePermPolicy
    scene_provider: IServerSceneProvider
    _metadata_provider: IServerMetadataProvider

    def _setup(
        self,
        plugin_manager: PluginSpecManager,
        session_manager: SceneSessionManager,
        scene_worker_manager: SceneWorkerManager,
        permission_policy: IScenePermPolicy,
        auth_policy: IAuthPolicy,
        scene_provider: IServerSceneProvider,
        metadata_provider: IServerMetadataProvider
    ):
        self.plugin_manager = plugin_manager
        self.session_manager = session_manager
        self.scene_worker_manager = scene_worker_manager
        
        self.scene_perm_policy = permission_policy
        self.auth_policy = auth_policy
        
        self.scene_provider = scene_provider
        self._metadata_provider = metadata_provider

    def _setup_plugins(self, plugins_folder: Path):
        PluginSubprocessHelper.setup_and_load_plugins(plugins_folder, self.plugin_manager)
        self._metadata_provider.setup_metadata()

    @property
    def metadata_provider(self) -> IMetadataProvider: 
        return self._metadata_provider
