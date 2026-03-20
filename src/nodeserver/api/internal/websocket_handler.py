from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.internal.websocket_protocol import WebsocketStatus
from nodeserver.api.server_instance import ServerInstance
import websockets
import json


class WebsocketHandler:
    instance_manager: InstanceManager
    connections: dict
    
    server_instance_type: type[ServerInstance] = ServerInstance
    
    def __init__(self, server_instance_type: type[ServerInstance]) -> None:
        self.server_instance_type = server_instance_type
        self.instance_manager = InstanceManager()
        self.connections = {}

    def on_disconnect(self, websocket):
        user_id = self.connections.pop(websocket, None)
        if user_id:
            instance = self.instance_manager.get_instance(user_id)
            if not instance:
                return
            
            # TODO: May kill the instance
            instance.save_state()
            instance.running = False
    
    async def on_handshake(self, websocket, user_id: str):
        new_instance: ServerInstance = self.server_instance_type()
        def _call_send_to_client(data: dict) -> None:
            WebsocketHandler._send_to_client(websocket, data)
        
        new_instance.set_output_callback(_call_send_to_client)
        success = self.instance_manager.set_instance(user_id, new_instance)
        if success:
            self.connections[websocket] = new_instance
            await websocket.send(json.dumps({"status": WebsocketStatus.CONNECTED, "session": user_id}))
            return
        
        await websocket.send(json.dumps({"status": WebsocketStatus.ERROR, "message": "Server might be full"}))


    async def on_message_received(self):
        pass


    @staticmethod
    def _send_to_client(websocket, data: dict):
        message = json.dumps(data)
        print(message)