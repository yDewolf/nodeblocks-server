import asyncio
from typing import Optional

from websockets.asyncio.server import ServerConnection
from nodeserver.api.instance.server_instance import ServerInstance
from nodeserver.api.utils.session_utils import UserSession, create_session_token, validate_session_token
from nodeserver.api.utils.url_routing import Endpoint, URLRouter
from nodeserver.api.internal.instance_manager import InstanceManager
import websockets
import json
import logging

from nodeserver.api.web.manager.session_manager import SessionManager
from nodeserver.api.web.message_router import BaseMessagerouter
from nodeserver.api.web.requests.websocket_requests import ServerMessage, SrvHandshakeError, SrvHandshakeSuccess
from nodeserver.api.web.websocket_messages import MessageUtils
from nodeserver.api.web.websocket_protocol import ServerMessages, WebsocketStatus

logger = logging.getLogger("nds.websocket")

class WebsocketHandler:
    instance_manager: InstanceManager
    session_manager: SessionManager

    loop: asyncio.AbstractEventLoop | None = None
    connections: dict[ServerConnection, ServerInstance] # type: ignore
    
    server_instance_type: type[ServerInstance] = ServerInstance
    _router: BaseMessagerouter
    _url_router: URLRouter

    def __init__(self, instance_manager: InstanceManager, session_manager: SessionManager, server_instance_type: type[ServerInstance], router_type: type[BaseMessagerouter]) -> None:
        self.server_instance_type = server_instance_type
        self.instance_manager = instance_manager
        self.session_manager = session_manager
        self._router = router_type()

        self._path_cache = {}
        self.connections = {}
        self._setup_routes()

    def _setup_routes(self):
        self._url_router = URLRouter({
            Endpoint("/instance/{user_id}", ["token"]): self.instance_listen_route,
        })

    def _set_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    def _process_request(self, connection, request: websockets.Request):
        self._path_cache[connection] = request.path
        return None

    async def main_router(self, websocket: ServerConnection):
        path = self._path_cache.get(websocket, "")
        try:
            route_stuff = self._url_router.route_url(path)
            if route_stuff:
                parameters, query_data, route_callable = route_stuff
                await route_callable(parameters, query_data, websocket)

            await websocket.close(1003, "Invalid Route")
            
        except websockets.ConnectionClosed:
            self.on_disconnect(websocket)
            
        finally:
            self.on_disconnect(websocket)

    # Server Stuff

    def on_disconnect(self, websocket):
        instance = self.connections.pop(websocket, None)
        if instance:
            instance_id = instance._attributed_id
            session = self.session_manager.get_session_by_instance(instance_id)
            
            if session:
                session.mark_disconnected()
                logger.info(f"Session '{instance_id}' disconnected. Entering grace period.")
            
            instance.stop_running()
            instance.save_internal_state()
    

    async def on_handshake(self, websocket: ServerConnection, user_id: str, token: Optional[str] = None):
        if self.instance_manager.is_full():
            await websocket.send(SrvHandshakeError(
                status=WebsocketStatus.DISCONNECTED,
                message="Server is full."
            ).model_dump_json())
            return
        
        instance, session, is_reconnection = self._prepare_socket_session(user_id, token)
        if not instance or not session:
            return

        def _thread_safe_send(data: ServerMessage) -> None:
            message = data.model_dump_json(by_alias=True)
            if self.loop:
                self.loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(websocket.send(message))
                )

        instance.set_send_callback(_thread_safe_send)
        self.connections[websocket] = instance

        type_data = instance.mirror_manager.type_reader.serialize_to_dict()
        await websocket.send(SrvHandshakeSuccess(
            status=WebsocketStatus.CONNECTED,
            session=session.token,
            type_data=type_data,
            reconnection=is_reconnection
        ).model_dump_json())

    def _prepare_socket_session(self, user_id: str, token: Optional[str] = None) -> tuple[Optional[ServerInstance], Optional[UserSession], bool]:
        session: Optional[UserSession] = None
        instance: Optional[ServerInstance] = None
        is_reconnection: bool = False
        
        if token:
            payload = validate_session_token(token)
            if payload:
                session = self.session_manager.get_session(token)
                
                if session:
                    instance = self.instance_manager.get_instance(session.instance_id)

        if not instance:
            instance = self.server_instance_type(self.instance_manager._default_types)
            instance._attributed_id = WebsocketHandler.make_instance_id(user_id)
            
            self.instance_manager.set_instance(instance._attributed_id, instance)
            logger.info(f"New Instance created for user {user_id}: {instance._attributed_id}")
        
        if session:
            is_reconnection = True
            session.mark_connected()
            logger.info(f"User {user_id} reconnected to instance {instance._attributed_id}")

        if not session:
            session = self.session_manager.start_session(user_id, instance._attributed_id)

        return (instance, session, is_reconnection)

    # Routes
    async def instance_listen_route(self, data: dict, query_data: dict, websocket: ServerConnection) -> dict | None:
        user_id = data.get("user_id")
        if user_id == None:
            # FIXME: Raise some exception
            return
        
        if user_id is None:
            await websocket.close(1008, "Missing user_id")
            return

        token = query_data.get("token", None)
        await self.on_handshake(websocket, user_id, token)
        await self._listen_loop(websocket)

    async def _listen_loop(self, websocket: ServerConnection) -> dict | None:
        instance = self.connections.get(websocket, None)
        async for message in websocket:
            try:
                data = json.loads(message)
                if instance == None:
                    continue

                out_data = await self._route_message(instance, data)
                if out_data:
                    await websocket.send(out_data.model_dump_json())

            except json.JSONDecodeError:
                continue
    
    async def _route_message(self, instance: ServerInstance, data: dict) -> ServerMessage | None:
        message = MessageUtils.parse_client_message(data)
        logger.info(f"Command Received: {message} for Instance '{instance._attributed_id}'")
        if not message:
            return
        
        output = self._router.route_message(message, instance)
        if output:
            logger.info(f"Sending route output to {instance} | output: {output.type}")
            logger.debug(f"Output Data: {output}")

        return output

    @staticmethod
    def make_instance_id(user_id: str):
        return f"{user_id}_{asyncio.get_event_loop().time()}"