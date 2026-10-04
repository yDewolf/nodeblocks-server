
import asyncio
import logging
from pathlib import Path
import time
from typing import Optional

from aiohttp import web

from nodeserver.engine.plugins.plugin_spec_manager import PluginSpecManager
from nodeserver.engine.registry.type_registry import TypeSpecRegistry
from nodeserver.engine.workers.scene.protocols.scene_worker_states import SceneWorkerExecutionState
from nodeserver.server.protocols.policies.auth_policy_protocol import IAuthPolicy
from nodeserver.server.protocols.policies.sceneperm_policy_protocol import IScenePermPolicy
from nodeserver.server.protocols.providers.scene_provider_protocol import IServerSceneProvider
from nodeserver.server.providers.scene_provider import SceneProvider
from nodeserver.server.web.app import NodeServerWebApp
from nodeserver.server.web.manager.scene_worker_manager import SceneWorkerManager
from nodeserver.server.web.manager.scene_session_manager import SceneSessionManager
from nodeserver.server.web.policies.dev_policies import DevAuthPolicy, DevScenePermPolicy
from nodeserver.server.web.policies.scene_permission_policy import FilePermissionPolicy
from nodeserver.server.web.routing.plugin_http_router import PluginHTTPRouter
from nodeserver.server.web.routing.scene_http_router import SceneHTTPRouter
from nodeserver.server.web.routing.scene_ws_router import SceneWebsocketRouter


logger = logging.getLogger("nds.server")
SCENE_WORKER_GRACE_PERIOD = 5 * 60 # seconds
INACTIVITY_CHECK_INTERVAL = 15.0 # seconds

# TODO: reimplement previous protocols
class NodeServer:
    app: NodeServerWebApp

    # TODO: Talvez fazer uma lista de routers
    scene_ws_router: SceneWebsocketRouter
    plugin_http_router: PluginHTTPRouter
    scene_http_router: SceneHTTPRouter

    plugins_folder: Path
    scenes_folder: Path

    host: str
    port: int

    _tasks: list[asyncio.Task]

    def __init__(
        self,
        plugins_folder: Path,
        scenes_folder: Path,
        permission_policy: Optional[IScenePermPolicy] = None,
        auth_policy: Optional[IAuthPolicy] = None,
        scene_provider: Optional[IServerSceneProvider] = None,
        host: str = "127.0.0.1",
        port: int = 8080
    ) -> None:
        self._tasks = []
        self.host = host
        self.port = port
        self.plugins_folder = plugins_folder
        self.scenes_folder = scenes_folder

        self.app = NodeServerWebApp()
        self.app.on_startup.append(self._on_startup)
        self.app.on_cleanup.append(self._on_cleanup)

        self.app._setup(
            PluginSpecManager.new(),
            SceneSessionManager(),
            SceneWorkerManager(self.plugins_folder, self.scenes_folder),
            permission_policy or FilePermissionPolicy(self.app),
            auth_policy or DevAuthPolicy(),
            scene_provider or SceneProvider(self.scenes_folder)
        )
        self.app._setup_plugins(self.plugins_folder)

        self.scene_ws_router = SceneWebsocketRouter(self.app)
        self.plugin_http_router = PluginHTTPRouter(self.app)
        self.scene_http_router = SceneHTTPRouter(self.app)
        self._setup_routes()


    def _setup_routes(self):
        self.plugin_http_router._setup_routes()
        self.scene_http_router._setup_routes()
        self.scene_ws_router._setup_routes()

    
    def run(self):
        web.run_app(self.app, host=self.host, port=self.port)


    async def _on_startup(self, app: web.Application):
        logger.info("Starting Nodeserver on %s:%s ...", self.host, self.port)
        self._tasks.append(
            asyncio.create_task(self._clear_inactive_workers_task(), name="inactivity_tracker")
        )
        await self.app.scene_worker_manager.start()

    async def _on_cleanup(self, app: web.Application):
        logger.info("Finishing Nodeserver. Cleaning subprocesses...")
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            logger.info("Finished server task: %s", task.get_name())
        
        await self.app.scene_worker_manager.stop()

    # Tasks and event handlers

    async def _clear_inactive_workers_task(self):
        while True:
            stopped_scenes = self.app.scene_worker_manager.get_scene_id_by_state(
                SceneWorkerExecutionState.STOPPED, min_elapsed_time=SCENE_WORKER_GRACE_PERIOD
            )
            for scene_id, timestamp in stopped_scenes:
                sessions = self.app.session_manager.get_scene_sessions(scene_id)
                if len(sessions) == 0:
                    logger.info("Killing %s's scene worker because of inactivity. Stopped since %s", scene_id, time.ctime(timestamp))
                    self.app.scene_worker_manager.kill_scene_worker(scene_id)
            
            await asyncio.sleep(INACTIVITY_CHECK_INTERVAL)
