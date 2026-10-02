
from json import JSONDecodeError
import logging
from pathlib import Path
from typing import Optional

from aiohttp import WSMsgType, web
from pydantic import ValidationError

from nodeserver.engine.workers.protocols.scene_worker_protocol import IPCSceneWorkerEvent
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.policies.perm_policy_protocol import BasePermissionPolicy, DevPermissionPolicy
from nodeserver.server.protocols.session_protocols import SceneConnectionSession, SceneSessionToken, UserSession
from nodeserver.server.protocols.web.session_messages import CreateSessionTokenModel
from nodeserver.server.web.app import NodeServerWebApp
from nodeserver.server.web.handlers.scene_websocket_handler import SceneWebsocketHandler
from nodeserver.server.web.manager.scene_worker_manager import SceneWorkerManager
from nodeserver.server.web.manager.scene_session_manager import SceneSessionManager


logger = logging.getLogger("nds.server")

# TODO: reimplement previous protocols
# TODO: implement scene grace period (stopped scenes without any connections)
class NodeServer:
    app: NodeServerWebApp

    plugins_folder: Path
    scenes_folder: Path

    host: str
    port: int

    session_manager: SceneSessionManager
    scene_worker_manager: SceneWorkerManager
    
    scene_websocket_handler: SceneWebsocketHandler 

    def __init__(
        self,
        plugins_folder: Path,
        scenes_folder: Path,
        permission_policy: Optional[BasePermissionPolicy] = None,
        host: str = "127.0.0.1",
        port: int = 8080
    ) -> None:
        self.host = host
        self.port = port
        self.plugins_folder = plugins_folder
        self.scenes_folder = scenes_folder

        self.permission_policy = permission_policy or DevPermissionPolicy()
        self.session_manager = SceneSessionManager()
        self.scene_worker_manager = SceneWorkerManager(self.plugins_folder, self.scenes_folder)

        self.scene_worker_manager.set_event_callback(self._on_worker_event)

        self.scene_websocket_handler = SceneWebsocketHandler(self.permission_policy, self.scene_worker_manager, self.session_manager)

        self.app = NodeServerWebApp()
        self.app.on_startup.append(self._on_startup)
        self.app.on_cleanup.append(self._on_cleanup)
        self.app.setup(
            self.session_manager,
            self.scene_worker_manager,
            self.permission_policy
        )

        self._setup_routes()


    def _setup_routes(self):
        self.app.router.add_post("/api/scene/{scene_id}", self.handle_scene_token_create)
        self.app.router.add_get("/ws/scene", self.handle_scene_websocket)

    
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

    # Route handlers

    async def handle_scene_websocket(self, request: web.Request) -> web.StreamResponse:
        token_str = request.query.get("token")
        if not token_str:
            raise web.HTTPUnauthorized(reason="Missing session token")

        try:
            token_payload = SceneSessionToken.from_token_str(token_str)
        except Exception:
            raise web.HTTPForbidden(reason="Invalid or expired session token")

        user = UserSession(user_id=token_payload.sub)
        return await self.scene_websocket_handler.handle_session_start(token_payload, user, request)

    async def handle_scene_token_create(self, request: web.Request):
        try:
            data = await request.json()
        except JSONDecodeError as e:
            return web.json_response({"error": "invalid_json", "message": str(e)})

        try:
            model_data = CreateSessionTokenModel.model_validate(data)
        except ValidationError as e:
            return web.json_response({"error": "invalid_body", "message": str(e)})
        
        scene_id = request.match_info["scene_id"]
        token = SceneSessionToken.new(model_data.user_id, scene_id)
        return web.json_response({
            "token": str(token),
            "scene_id": scene_id
        })

