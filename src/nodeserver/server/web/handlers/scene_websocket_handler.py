import logging
from aiohttp import web

from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.policies.perm_policy_protocol import BasePermissionPolicy
from nodeserver.server.protocols.session_protocols import SceneConnectionSession, SceneSessionToken, UserSession
from nodeserver.server.web.manager.scene_session_manager import SceneSessionManager
from nodeserver.server.web.manager.scene_worker_manager import SceneWorkerManager

logger = logging.getLogger("nds.server") # TODO: talvez separar em nds.websocket

class SceneWebsocketHandler:
    permission_policy: BasePermissionPolicy
    scene_worker_manager: SceneWorkerManager
    session_manager: SceneSessionManager

    def __init__(
        self,
        permission_policy: BasePermissionPolicy,
        scene_worker_manager: SceneWorkerManager,
        session_manager: SceneSessionManager
    ) -> None:
        self.permission_policy = permission_policy
        self.scene_worker_manager = scene_worker_manager
        self.session_manager = session_manager


    async def socket_listen_loop(self, socket: web.WebSocketResponse, session: SceneConnectionSession):
        try:
            async for msg in socket:
                logger.info("Received message %s from %s", msg, session.user.user_id)
                pass # TODO: handle client commands
            
        finally:
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
