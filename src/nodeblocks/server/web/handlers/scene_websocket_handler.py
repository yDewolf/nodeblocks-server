import logging
from aiohttp import WSMsgType, web

from nodeblocks.engine.workers.scene.protocols.scene_worker_protocol import SceneWorkerCommandResponse
from nodeblocks.server.protocols.permission.scene_permissions import ScenePermission
from nodeblocks.server.protocols.policies.sceneperm_policy_protocol import IScenePermPolicy
from nodeblocks.server.protocols.session.session_protocols import SceneConnectionSession, SceneSessionToken, UserSession
from nodeblocks.server.protocols.web.messages.client.base_client_command import CommandGroups
from nodeblocks.server.protocols.web.messages.server.mappings.cmd_response_map import get_response_payload
from nodeblocks.server.protocols.web.messages.server.server_messages import ServerCmdResponse
from nodeblocks.server.web.dispatchers.scene_command_dispatcher import WSSceneCommandDispatcher
from nodeblocks.server.web.exceptions.cmd_dispatcher_exceptions import ServerCmdDispatchError
from nodeblocks.server.web.handlers.base_command_handler import BaseSceneCmdHandler
from nodeblocks.server.web.handlers.command.execution_command_handler import ExecutionCommandHandler
from nodeblocks.server.web.handlers.command.graph_command_handler import GraphCommandHandler
from nodeblocks.server.web.handlers.command.scene_command_handler import SceneCommandHandler
from nodeblocks.server.web.manager.scene_session_manager import SceneSessionManager
from nodeblocks.server.web.manager.scene_worker_manager import SceneWorkerManager

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
        })


    async def socket_listen_loop(self, socket: web.WebSocketResponse, session: SceneConnectionSession):
        while True:
            try:
                async for msg in socket:
                    if msg.type == WSMsgType.TEXT:
                        logger.debug("Received message from %s", session.user.user_id)
                        try:
                            data = msg.json()
                            try: 
                                await self.dispatcher.dispatch(data, session, self.scene_worker_manager)
                            except ServerCmdDispatchError as e:
                                await self.session_manager.broadcast_to_scene(
                                    scene_id=session.scene_id,
                                    message=ServerCmdResponse(
                                        cmd_uid=e.cmd_uid or "",
                                        response_payload=get_response_payload(SceneWorkerCommandResponse.failed(
                                            request_id=e.cmd_uid,
                                            message=e.message
                                        ))
                                    )
                                )

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

    

    async def handle_session_start(self, token_payload: SceneSessionToken, user: UserSession, use_protoc: bool, request: web.Request) -> web.StreamResponse:
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
            socket=socket,
            use_protoc=use_protoc
        )
        
        self.session_manager.register_connection(session)
        await self.socket_listen_loop(socket, session)
        return socket
