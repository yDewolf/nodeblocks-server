import asyncio

from websockets.asyncio.server import ServerConnection
from nodeserver.api.web.command_router import BaseCommandRouter
from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.internal.websocket_protocol import WebsocketStatus
from nodeserver.api.server_instance import ServerInstance
import websockets
import json
import logging


WEBSOCKET_LOGGER = logging.Logger("WebsocketLogger")

class WebsocketHandler:
    instance_manager: InstanceManager

    loop: asyncio.AbstractEventLoop | None = None
    connections: dict[ServerConnection, ServerInstance] # type: ignore
    
    server_instance_type: type[ServerInstance] = ServerInstance
    _router: BaseCommandRouter

    def __init__(self, instance_manager: InstanceManager, server_instance_type: type[ServerInstance], router_type: type[BaseCommandRouter]) -> None:
        self.server_instance_type = server_instance_type
        self.instance_manager = instance_manager
        self._router = router_type()

        self._path_cache = {}
        self.connections = {}

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    def process_request(self, connection, request: websockets.Request):
        self._path_cache[connection] = request.path
        return None

    async def main_router(self, websocket):
        path = self._path_cache.get(websocket, "")
        parts = path.strip("/").split("/")

        try:
            if len(parts) >= 2 and parts[0] == "instance":
                user_id = parts[1]
                if len(parts) == 2:
                    await self.on_handshake(websocket, user_id)
                    await self.listen_loop(websocket)
                    return

            await websocket.close(1003, "Invalid Route")
            
        except websockets.ConnectionClosed:
            pass
    
        finally:
            self.on_disconnect(websocket)

    async def listen_loop(self, websocket):
        instance = self.connections.get(websocket, None)
        async for message in websocket:
            try:
                data = json.loads(message)
                if instance == None:
                    continue

                out_data = await self.route_message(instance, data)
                if out_data:
                    await websocket.send(json.dumps(out_data))

            except json.JSONDecodeError:
                continue
    
    async def route_message(self, instance: ServerInstance, data: dict) -> dict | None:
        msg_type = str(data.get("type", ""))
        WEBSOCKET_LOGGER.info(f"[WS] Command Received: {data.get('type')} for Instance {instance._attributed_id}")
        payload = data.get("payload", {})
        if not type(payload) is dict:
            return
        
        return self._router.route_message(msg_type, payload, instance)


    def on_disconnect(self, websocket):
        instance = self.connections.pop(websocket, None)
        if instance:
            if not instance:
                return

            self.instance_manager.remove_instance(instance._attributed_id)
            instance.stop_running()            
            instance.save_state()
            WEBSOCKET_LOGGER.info("user disconnected")
    

    async def on_handshake(self, websocket, user_id: str):
        new_instance: ServerInstance = self.server_instance_type(self.instance_manager._default_types)
        new_instance._attributed_id = user_id

        def _thread_safe_send(data: dict) -> None:
            message = json.dumps(data)

            WEBSOCKET_LOGGER.debug(f"sending: {message}")
            if self.loop:
                self.loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(websocket.send(message))
                )
        
        new_instance.set_output_callback(_thread_safe_send)
        success = self.instance_manager.set_instance(user_id, new_instance)
        if success:
            self.connections[websocket] = new_instance
            type_data = new_instance.mirror_manager.type_reader.serialize_to_dict()
            await websocket.send(json.dumps({"status": WebsocketStatus.CONNECTED.value, "session": user_id, "type_data": type_data}))
            return
        
        await websocket.send(json.dumps({"status": WebsocketStatus.ERROR.value, "message": "Server might be full"}))
