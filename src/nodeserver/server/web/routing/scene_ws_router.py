import logging
from typing import Optional

from aiohttp import web

from nodeserver.engine.workers.protocols.general_worker_protocol import EvtWorkerReady, WorkerEvent
from nodeserver.engine.workers.scene.protocols.scene_worker_protocol import IPCSceneWorkerEvent, SceneWorkerCommandResponse, WorkerEngineEventWrapper
from nodeserver.server.protocols.session_protocols import SceneSessionToken, UserSession
from nodeserver.server.protocols.web.messages.server.mappings.worker_event_map import get_worker_event_payload
from nodeserver.server.protocols.web.messages.server.server_messages import ServerCmdResponse, BaseServerMessage, ServerEngineEventWrapper, ServerWorkerEventWrapper
from nodeserver.server.protocols.web.messages.server.mappings.cmd_response_map import get_response_payload
from nodeserver.server.protocols.web.messages.server.mappings.engine_event_map import get_engine_event_payload
from nodeserver.server.web.app import NodeServerWebApp
from nodeserver.server.web.handlers.scene_websocket_handler import SceneWebsocketHandler
from nodeserver.server.web.routing.base_router import BaseRouter

logger = logging.getLogger("nds.server")

class SceneWebsocketRouter(BaseRouter):
    scene_websocket_handler: SceneWebsocketHandler

    def __init__(self, app: NodeServerWebApp) -> None:
        super().__init__(app)
        self.scene_websocket_handler = SceneWebsocketHandler(
            self.app.scene_perm_policy, 
            self.app.scene_worker_manager, 
            self.app.session_manager
        )
        self.app.scene_worker_manager.set_event_callback(self._on_worker_event)

    # Called by NodeServer
    def _setup_routes(self):
        self.app.router.add_get("/ws/scene", self.handle_scene_websocket)


    async def _on_worker_event(self, scene_id: str, event: IPCSceneWorkerEvent):
        logger.debug("Event from scene: '%s': %s", scene_id, event)
        message: Optional[BaseServerMessage] = None
        if isinstance(event, SceneWorkerCommandResponse):
            if not event.request_id: 
                # FIXME: exception
                raise Exception("Command response is missing request id (command id)")

            message = ServerCmdResponse(
                cmd_uid=event.request_id,
                response_payload=get_response_payload(event)
            )

        elif isinstance(event, WorkerEvent):
            message = ServerWorkerEventWrapper(
                event_payload=get_worker_event_payload(event)
            )

        elif isinstance(event, WorkerEngineEventWrapper):
            message = ServerEngineEventWrapper(
                event_payload=get_engine_event_payload(event.engine_event),
            )

        if not message:
            logger.error("No wrap implementation for engine event: %s", event)
            raise Exception(f"Unhandled worker event: {event}")

        await self.app.session_manager.broadcast_to_scene(
            scene_id=scene_id, 
            message=message
        )
    

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
