
import logging
from pathlib import Path
from typing import Optional

from aiohttp import web

from nodeserver.engine.workers.protocols.scene_worker_protocol import IPCSceneWorkerEvent
from nodeserver.server.protocols.policies.perm_policy_protocol import BasePermissionPolicy, DevPermissionPolicy
from nodeserver.server.web.app import NodeServerWebApp
from nodeserver.server.web.manager.scene_worker_manager import SceneWorkerManager
from nodeserver.server.web.manager.scene_session_manager import SceneSessionManager


logger = logging.getLogger("nds.server")

# TODO: reimplement previous protocols
# TODO: implement scene grace period (stopped scenes without any connections)
class NodeServer:
    app: NodeServerWebApp

    plugins_folder: Path
    host: str
    port: int

    session_manager: SceneSessionManager
    scene_worker_manager: SceneWorkerManager

    def __init__(
        self,
        plugins_folder: Path,
        permission_policy: Optional[BasePermissionPolicy] = None,
        host: str = "127.0.0.1",
        port: int = 8080
    ) -> None:
        self.host = host
        self.port = port
        self.plugins_folder = plugins_folder

        self.session_manager = SceneSessionManager()
        self.scene_worker_manager = SceneWorkerManager(self.plugins_folder)
        self.permission_policy = permission_policy or DevPermissionPolicy()

        self.scene_worker_manager.set_event_callback(self._on_worker_event)

        self.app = NodeServerWebApp()
        self.app.on_startup.append(self._on_startup)
        self.app.on_cleanup.append(self._on_cleanup)
        self.app.setup(
            self.session_manager,
            self.scene_worker_manager,
            self.permission_policy
        )
        
    def run(self):
        web.run_app(self.app, host=self.host, port=self.port)


    async def _on_startup(self, app: web.Application):
        logger.info("Starting Nodeserver on %s:%s...", self.host, self.port)
        await self.scene_worker_manager.start()

    async def _on_cleanup(self, app: web.Application):
        logger.info("Finishing Nodeserver. Cleaning subprocesses...")
        await self.scene_worker_manager.stop()


    async def _on_worker_event(self, scene_id: str, event: IPCSceneWorkerEvent):
        logger.debug("Event from scene: '%s': %s", scene_id, event)
        # TODO: pydantic model based websocket messages
        await self.session_manager.broadcast_to_scene(
            scene_id=scene_id, 
            message={
                "type": "SCENE_EVENT",
                "event_type": event.__class__.__name__,
                "data": event.__dict__
            }
        )
