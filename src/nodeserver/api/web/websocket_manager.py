import asyncio
import websockets

from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.internal.websocket_handler import WebsocketHandler
from nodeserver.api.server_instance import ServerInstance
from nodeserver.networking.nodes.helpers.file.typing_file_reader import TypeFileReader

class WebsocketInstanceManager(InstanceManager):
    loop: asyncio.AbstractEventLoop
    host: str
    port: int
    handler: WebsocketHandler

    stop: asyncio.Future | None

    def __init__(self, default_types: TypeFileReader | None = None, host="0.0.0.0", port=3001):
        super().__init__(default_types)
        self.handler = WebsocketHandler(self, ServerInstance)
        
        self.host = host
        self.port = port


    async def run_server(self):
        self.loop = asyncio.get_event_loop()
        self.handler.set_loop(self.loop)
        
        self.stop = asyncio.get_running_loop().create_future()
        
        async with websockets.serve(self.handler.main_router, self.host, self.port, process_request=self.handler.process_request):
            print(f"Node Server Headless rodando em ws://{self.host}:{self.port}")
            await self.stop