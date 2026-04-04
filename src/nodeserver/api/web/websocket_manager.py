import asyncio
from websockets.asyncio.server import serve

from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.internal.websocket_handler import WebsocketHandler
from nodeserver.api.server_instance import ServerInstance
from nodeserver.api.web.command_router import BaseCommandRouter
from nodeserver.networking.nodes.helpers.file.typing_file_reader import TypeFileReader

import logging
logger = logging.getLogger("nds.websocket")

class WebsocketInstanceManager(InstanceManager):
    loop: asyncio.AbstractEventLoop
    host: str
    port: int
    handler: WebsocketHandler

    stop: asyncio.Future | None

    def __init__(self, default_types: TypeFileReader | None = None, host="0.0.0.0", port=3001):
        super().__init__(default_types)
        self.handler = WebsocketHandler(self, ServerInstance, BaseCommandRouter)
        
        self.host = host
        self.port = port


    async def run_server(self):
        self.loop = asyncio.get_event_loop()
        self.handler._set_loop(self.loop)

        self.stop = asyncio.get_running_loop().create_future()
        
        async with serve(
            self.handler.main_router, 
            self.host, self.port, 
            process_request=self.handler._process_request,
            ping_interval=5,
            ping_timeout=5,
            close_timeout=1
        ):
            logger.info(f"Node Server Headless rodando em ws://{self.host}:{self.port}")
            await self.stop