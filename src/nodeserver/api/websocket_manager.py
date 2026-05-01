import asyncio
from aiohttp import web

from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.web.manager.session_manager import SessionManager
from nodeserver.api.web.manager.websocket_handler import WebsocketHandler
from nodeserver.api.instance.server_instance import ServerInstance
from nodeserver.api.web.message_router import BaseMessagerouter
import logging

logger = logging.getLogger("nds.websocket")

class WebsocketManager:
    loop: asyncio.AbstractEventLoop | None = None
    host: str
    port: int

    handler: WebsocketHandler
    instance_manager: InstanceManager

    stop: asyncio.Future | None

    def __init__(self, instance_manager: InstanceManager, session_manager: SessionManager, server_intance_type: type[ServerInstance], host: str, port: int):
        self.instance_manager = instance_manager
        self.handler = WebsocketHandler(self.instance_manager, session_manager, server_intance_type, BaseMessagerouter)
        
        self.host = host
        self.port = port

    async def handle_connection(self, ws: web.WebSocketResponse, request: web.Request):
        await self.handler.main_router(ws, request)

        return ws
    
    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.handler.loop = self.loop
