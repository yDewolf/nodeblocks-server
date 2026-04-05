import asyncio

from websockets.asyncio.server import ServerConnection
from nodeserver.api.internal.websocket_messages import MessageUtils
from nodeserver.api.utils.url_routing import Endpoint, URLRouter
from nodeserver.api.web.command_router import BaseCommandRouter
from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.internal.websocket_protocol import ServerMessages, WebsocketStatus
from nodeserver.api.server_instance import ServerInstance
import websockets
import json
import logging

logger = logging.getLogger("nds.websocket")

class WebsocketHandler:
    instance_manager: InstanceManager

    loop: asyncio.AbstractEventLoop | None = None
    connections: dict[ServerConnection, ServerInstance] # type: ignore
    
    server_instance_type: type[ServerInstance] = ServerInstance
    _router: BaseCommandRouter
    _url_router: URLRouter

    def __init__(self, instance_manager: InstanceManager, server_instance_type: type[ServerInstance], router_type: type[BaseCommandRouter]) -> None:
        self.server_instance_type = server_instance_type
        self.instance_manager = instance_manager
        self._router = router_type()

        self._path_cache = {}
        self.connections = {}
        self._setup_routes()

    def _setup_routes(self):
        self._url_router = URLRouter({
            Endpoint("/instance/{user_id}"): self.instance_listen_route,
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
                parameters, route_callable = route_stuff
                await route_callable(parameters, websocket)

            await websocket.close(1003, "Invalid Route")
            
        except websockets.ConnectionClosed:
            self.on_disconnect(websocket)
            
        finally:
            self.on_disconnect(websocket)

    # Server Stuff

    def on_disconnect(self, websocket):
        instance = self.connections.pop(websocket, None)
        if instance:
            if not instance:
                return

            self.instance_manager.remove_instance(instance._attributed_id)
            instance.stop_running()            
            instance.save_internal_state()
            logger.info("user disconnected")
    
    async def on_handshake(self, websocket: ServerConnection, user_id: str):
        existing_instance = self.instance_manager.get_instance(user_id)
        new_instance: ServerInstance | None = None
        success = True
        if existing_instance:
            logger.info(f"Connecting Websocket to Existing instance {user_id}")
            new_instance = existing_instance
        
        else:
            new_instance = self.server_instance_type(self.instance_manager._default_types)
            new_instance._attributed_id = user_id
            success = self.instance_manager.set_instance(user_id, new_instance)

        def _thread_safe_send(data: dict) -> None:
            message = json.dumps(data)

            logger.debug(f"sending: {message}")
            if self.loop:
                self.loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(websocket.send(message))
                )

        new_instance.set_send_callback(_thread_safe_send)
        if success:
            self.connections[websocket] = new_instance
            type_data = new_instance.mirror_manager.type_reader.serialize_to_dict()
            logger.info(f"Connected websocket to instance {user_id}")
            await websocket.send(json.dumps({"type": ServerMessages.HANDSHAKE_SYNC.value, "status": WebsocketStatus.CONNECTED.value, "session": user_id, "type_data": type_data}))
            return
        
        logger.info("Couldn't connect websocket to instance")
        await websocket.send(json.dumps({"status": WebsocketStatus.ERROR.value, "message": "Server might be full"}))

    # Routes
    async def instance_listen_route(self, data: dict, websocket: ServerConnection) -> dict | None:
        user_id = data.get("user_id")
        if user_id == None:
            # FIXME: Raise some exception
            return
        
        await self.on_handshake(websocket, user_id)
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
                    await websocket.send(json.dumps(out_data))

            except json.JSONDecodeError:
                continue
    
    async def _route_message(self, instance: ServerInstance, data: dict) -> dict | None:
        message = MessageUtils.client_from_dict(data)
        logger.info(f"Command Received: {message} for Instance '{instance._attributed_id}'")
        if not message:
            return
        
        output = self._router.route_message(message, instance)
        if output:
            logger.info(f"Sending route output to {instance} | output: {output}")

        return output
