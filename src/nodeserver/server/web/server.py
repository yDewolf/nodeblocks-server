
import asyncio
import logging
from pathlib import Path
import time
from typing import Optional

from aiohttp import web

from nodeserver.engine.workers.scene.protocols.scene_worker_states import SceneWorkerExecutionState
from nodeserver.server.protocols.policies.perm_policy_protocol import BasePermissionPolicy, DevPermissionPolicy
from nodeserver.server.web.app import NodeServerWebApp
from nodeserver.server.web.manager.scene_worker_manager import SceneWorkerManager
from nodeserver.server.web.manager.scene_session_manager import SceneSessionManager
from nodeserver.server.web.routing.scene_ws_router import SceneWebsocketRouter


logger = logging.getLogger("nds.server")
SCENE_WORKER_GRACE_PERIOD = 5 * 60 # seconds
INACTIVITY_CHECK_INTERVAL = 15.0 # seconds

# TODO: reimplement previous protocols
class NodeServer:
    app: NodeServerWebApp
    scene_ws_router: SceneWebsocketRouter

    plugins_folder: Path
    scenes_folder: Path

    host: str
    port: int

    session_manager: SceneSessionManager
    scene_worker_manager: SceneWorkerManager
    
    _tasks: list[asyncio.Task]

    def __init__(
        self,
        plugins_folder: Path,
        scenes_folder: Path,
        permission_policy: Optional[BasePermissionPolicy] = None,
        host: str = "127.0.0.1",
        port: int = 8080
    ) -> None:
        self._tasks = []
        self.host = host
        self.port = port
        self.plugins_folder = plugins_folder
        self.scenes_folder = scenes_folder

        self.permission_policy = permission_policy or DevPermissionPolicy()
        self.session_manager = SceneSessionManager()
        self.scene_worker_manager = SceneWorkerManager(self.plugins_folder, self.scenes_folder)

        self.app = NodeServerWebApp()
        self.app.on_startup.append(self._on_startup)
        self.app.on_cleanup.append(self._on_cleanup)
        self.app.setup(
            self.session_manager,
            self.scene_worker_manager,
            self.permission_policy
        )

        self.scene_ws_router = SceneWebsocketRouter(self.app)
        self._setup_routes()


    def _setup_routes(self):
        self.scene_ws_router._setup_routes()

    
    def run(self):
        web.run_app(self.app, host=self.host, port=self.port)


    async def _on_startup(self, app: web.Application):
        logger.info("Starting Nodeserver on %s:%s...", self.host, self.port)
        self._tasks.append(
            asyncio.create_task(self._clear_inactive_workers_task())
        )
        await self.scene_worker_manager.start()

    async def _on_cleanup(self, app: web.Application):
        logger.info("Finishing Nodeserver. Cleaning subprocesses...")
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        await self.scene_worker_manager.stop()

    # Tasks and event handlers

    async def _clear_inactive_workers_task(self):
        while True:
            stopped_scenes = self.scene_worker_manager.get_scene_id_by_state(
                SceneWorkerExecutionState.STOPPED, min_elapsed_time=SCENE_WORKER_GRACE_PERIOD
            )
            for scene_id, timestamp in stopped_scenes:
                sessions = self.session_manager.get_scene_sessions(scene_id)
                if len(sessions) == 0:
                    logger.info("Killing %s's scene worker because of inactivity. Stopped since %s", scene_id, time.ctime(timestamp))
                    self.scene_worker_manager.kill_scene_worker(scene_id)
            
            await asyncio.sleep(INACTIVITY_CHECK_INTERVAL)
