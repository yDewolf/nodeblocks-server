import asyncio

from websockets.server import ServerConnection

from nodeserver.api.instance_states import InstanceCommands, InstanceStates, LoopStates
from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.internal.websocket_protocol import WebsocketStatus
from nodeserver.api.server_instance import ServerInstance
import websockets
import json

class WebsocketHandler:
    instance_manager: InstanceManager

    loop: asyncio.AbstractEventLoop | None = None
    connections: dict[ServerConnection, ServerInstance] # type: ignore
    
    server_instance_type: type[ServerInstance] = ServerInstance
    
    def __init__(self, instance_manager: InstanceManager, server_instance_type: type[ServerInstance]) -> None:
        self.server_instance_type = server_instance_type
        self.instance_manager = instance_manager

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
                await self.on_handshake(websocket, user_id)
                await self.listen_loop(websocket)
            else:
                websocket.send_close(1003, "Invalid Route")

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

                await self.route_message(instance, data)
            
            except json.JSONDecodeError:
                continue
    
    async def route_message(self, instance: ServerInstance, data: dict):
        msg_type = str(data.get("type", ""))
        print(f"[WS] Command Received: {data.get('type')} for Instance {instance._attributed_id}")
        
        payload = data.get("payload", {})
        if not type(payload) is dict:
            return
        
        match msg_type.upper():
            case "SET_STATE":
                try:
                    new_state = InstanceStates(payload.get("state", -1))
                    instance.state_controller.queue_state(new_state)
                except ValueError:
                    pass

            case "SET_LOOP_STATE":
                try:
                    new_state = LoopStates(payload.get("state", -1))
                    instance.state_controller.queue_loop_state(new_state)
                except ValueError:
                    pass

            case "RUN":
                instance.start_running()
            case "RESUME":
                instance.state_controller.command_queue.put(InstanceCommands.RESUME_LOOP)
            case "STOP":
                instance.state_controller.command_queue.put(InstanceCommands.STOP)
            case "STEP":
                instance.state_controller.command_queue.put(InstanceCommands.STEP_NEXT)
            case "LOAD_SCENE":
                instance.load_new_scene(payload)
            
            case _:
                print(f"Unknown command: {msg_type}")


    def on_disconnect(self, websocket):
        instance = self.connections.pop(websocket, None)
        if instance:
            if not instance:
                return

            self.instance_manager.remove_instance(instance._attributed_id)
            instance.stop_running()            
            instance.save_state()
            print("user disconnected")
    

    async def on_handshake(self, websocket, user_id: str):
        new_instance: ServerInstance = self.server_instance_type(self.instance_manager._default_types)
        new_instance._attributed_id = user_id

        def _thread_safe_send(data: dict) -> None:
            message = json.dumps(data)

            print(f"sending: {message}")
            if self.loop:
                self.loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(websocket.send(message))
                )
        
        new_instance.set_output_callback(_thread_safe_send)
        success = self.instance_manager.set_instance(user_id, new_instance)
        if success:
            self.connections[websocket] = new_instance
            await websocket.send(json.dumps({"status": WebsocketStatus.CONNECTED.value, "session": user_id}))
            return
        
        await websocket.send(json.dumps({"status": WebsocketStatus.ERROR.value, "message": "Server might be full"}))
