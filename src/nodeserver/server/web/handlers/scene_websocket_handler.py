import logging
from aiohttp import WSMsgType, web

from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.policies.sceneperm_policy_protocol import IScenePermPolicy
from nodeserver.server.protocols.session_protocols import SceneConnectionSession, SceneSessionToken, UserSession
from nodeserver.server.protocols.web.messages.client.base_client_command import CommandGroups
from nodeserver.server.web.dispatchers.scene_command_dispatcher import WSSceneCommandDispatcher
from nodeserver.server.web.handlers.base_command_handler import BaseSceneCmdHandler
from nodeserver.server.web.handlers.command.execution_command_handler import ExecutionCommandHandler
from nodeserver.server.web.handlers.command.graph_command_handler import GraphCommandHandler
from nodeserver.server.web.handlers.command.scene_command_handler import SceneCommandHandler
from nodeserver.server.web.manager.scene_session_manager import SceneSessionManager
from nodeserver.server.web.manager.scene_worker_manager import SceneWorkerManager

logger = logging.getLogger("nds.server") # TODO: talvez separar em nds.websocket

class SceneWebsocketHandler:
    permission_policy: IScenePermPolicy
    scene_worker_manager: SceneWorkerManager
    session_manager: SceneSessionManager
    dispatcher: WSSceneCommandDispatcher

    def __init__(
        self,
        scene_perm_policy: IScenePermPolicy,
        scene_worker_manager: SceneWorkerManager,
        session_manager: SceneSessionManager,
    ) -> None:
        self.permission_policy = scene_perm_policy
        self.scene_worker_manager = scene_worker_manager
        self.session_manager = session_manager

        # FIXME: talvez declarar os handlers em outro lugar
        self.dispatcher = WSSceneCommandDispatcher({
            CommandGroups.GRAPH: GraphCommandHandler(),
            CommandGroups.SCENE: SceneCommandHandler(),
            CommandGroups.EXECUTION: ExecutionCommandHandler(),
            # TODO: notification command handler
        })


    async def socket_listen_loop(self, socket: web.WebSocketResponse, session: SceneConnectionSession):
        while True:
            try:
                async for msg in socket:
                    if msg.type == WSMsgType.TEXT:
                        logger.debug("Received message from %s", session.user.user_id)
                        try:
                            data = msg.json()
                            await self.dispatcher.dispatch(data, session, self.scene_worker_manager)
                        except ValueError as e:
                            await socket.send_json({"error": "invalid_body", "message": str(e)})
                    
                    elif msg.type == WSMsgType.ERROR:
                        logger.error("WebSocket connection closed with exception %s", socket.exception())
                        break
            except RuntimeError:
                break

            except Exception as e:
                logger.warning("Websocket Exception: %s", e)
            
        logger.warning("Closed Scene Connection: %s - Scene id: %s", session.id, session.scene_id)
        self.session_manager.unregister_connection(session.id)

    

    async def handle_session_start(self, token_payload: SceneSessionToken, user: UserSession, request: web.Request) -> web.StreamResponse:
        permissions = await self.permission_policy.get_scene_permissions(user, token_payload.sid)
        if not (ScenePermission.READ in permissions):
            raise web.HTTPForbidden(reason="Insufficient permissions to access scene")
        
        self.scene_worker_manager.get_or_create_worker(token_payload.sid)

        socket = web.WebSocketResponse()
        await socket.prepare(request)

        session = SceneConnectionSession(
            token_payload=token_payload,
            user=user,
            permissions=permissions,
            socket=socket
        )
        self.session_manager.register_connection(session)
        # TODO: send handshake
        # await socket.send_json({
        #     "type": "HANDSHAKE_ACK",
        #     "connection_id": session.id,
        #     "scene_id": session.scene_id
        # })
        await self.socket_listen_loop(socket, session)
        return socket
