from pathlib import Path
from aiohttp import web

from nodeblocks.engine.helpers.plugin_subprocess_helper import PluginSubprocessHelper
from nodeblocks.engine.plugins.plugin_spec_manager import PluginSpecManager
from nodeblocks.server.protocols.policies.auth_policy_protocol import IAuthPolicy
from nodeblocks.server.protocols.policies.sceneperm_policy_protocol import IScenePermPolicy
from nodeblocks.server.protocols.policies.server_session_policy import IServerSessionPolicy
from nodeblocks.server.protocols.providers.artifact_provider_protocol import IServerSceneArtifactProvider
from nodeblocks.server.protocols.providers.metadata_provider_protocol import IMetadataProvider, IServerMetadataProvider
from nodeblocks.server.protocols.providers.scene_provider_protocol import IServerSceneProvider
from nodeblocks.server.web.manager.scene_worker_manager import SceneWorkerManager
from nodeblocks.server.web.manager.scene_session_manager import SceneSessionManager
from nodeblocks.server.web.manager.server_session_manager import ServerSessionManager


class NodeServerWebApp(web.Application):
    # TODO: separar algumas coisas aqui em módulos diferentes
    plugin_manager: PluginSpecManager
    server_session_manager: ServerSessionManager
    scene_session_manager: SceneSessionManager
    scene_worker_manager: SceneWorkerManager

    auth_policy: IAuthPolicy
    session_policy: IServerSessionPolicy
    scene_perm_policy: IScenePermPolicy
    scene_provider: IServerSceneProvider

    scene_artifact_provider: IServerSceneArtifactProvider

    _metadata_provider: IServerMetadataProvider

    def _setup(
        self,
        plugin_manager: PluginSpecManager,
        server_session_manager: ServerSessionManager,
        scene_session_manager: SceneSessionManager,
        scene_worker_manager: SceneWorkerManager,

        permission_policy: IScenePermPolicy,
        auth_policy: IAuthPolicy,
        session_policy: IServerSessionPolicy,
        scene_provider: IServerSceneProvider,
        scene_artifact_provider: IServerSceneArtifactProvider,
        metadata_provider: IServerMetadataProvider
    ):
        self.plugin_manager = plugin_manager
        self.server_session_manager = server_session_manager
        self.scene_session_manager = scene_session_manager
        self.scene_worker_manager = scene_worker_manager
        
        self.scene_perm_policy = permission_policy
        self.auth_policy = auth_policy
        self.session_policy = session_policy
        
        self.scene_provider = scene_provider
        self.scene_artifact_provider = scene_artifact_provider

        self._metadata_provider = metadata_provider

    def _setup_plugins(self, plugins_folder: Path, extraction_folder: Path):
        # TODO: implementar state DTOs para permitir que a engine seja usada
        # para atualizar o estado atual do servidor
        PluginSubprocessHelper.setup_and_load_plugins(plugins_folder, extraction_folder, self.plugin_manager, allow_install=True)
        self._metadata_provider.setup_metadata()

    @property
    def metadata_provider(self) -> IMetadataProvider: 
        return self._metadata_provider
