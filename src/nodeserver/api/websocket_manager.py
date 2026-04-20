import asyncio
from websockets.asyncio.server import serve

from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.web.manager.session_manager import SessionManager
from nodeserver.api.web.manager.websocket_handler import WebsocketHandler
from nodeserver.api.instance.server_instance import ServerInstance
from nodeserver.api.web.message_router import BaseMessagerouter
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import TypeFileReader
import logging

logger = logging.getLogger("nds.websocket")

class WebsocketInstanceManager(InstanceManager):
    loop: asyncio.AbstractEventLoop
    host: str
    port: int

    handler: WebsocketHandler
    session_manager: SessionManager

    stop: asyncio.Future | None

    def __init__(self, default_types: TypeFileReader | None = None, host="0.0.0.0", port=3001):
        super().__init__(default_types)
        self.session_manager = SessionManager()
        self.handler = WebsocketHandler(self, self.session_manager, ServerInstance, BaseMessagerouter)
        
        self.host = host
        self.port = port


    async def run_server(self):
        self.loop = asyncio.get_running_loop()
        self.handler._set_loop(self.loop)

        self.stop = asyncio.get_running_loop().create_future()
        self.loop.create_task(self._clean_sessions_task())

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
    
    async def _clean_sessions_task(self):
        while True:
            await asyncio.sleep(3.0)

            removed_sessions = self.session_manager._clean_inactive_sessions()
            for session in removed_sessions:
                self.remove_instance(session.instance_id)
                logger.info(f"Removing inactive Instance {session.instance_id}")
        pass