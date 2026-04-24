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
    loop: asyncio.AbstractEventLoop | None
    host: str
    port: int

    handler: WebsocketHandler
    session_manager: SessionManager
    instance_manager: InstanceManager

    stop: asyncio.Future | None

    def __init__(self, instance_manager: InstanceManager, host: str, port: int):
        self.session_manager = SessionManager()
        self.instance_manager = instance_manager
        self.handler = WebsocketHandler(self.instance_manager, self.session_manager, ServerInstance, BaseMessagerouter)
        
        self.host = host
        self.port = port

    async def handle_connection(self, ws: web.WebSocketResponse, request: web.Request):
        await self.handler.main_router(ws, request)

        return ws
    
    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.handler.loop = self.loop


    async def _clean_sessions_task(self):
        while True:
            await asyncio.sleep(3.0)

            removed_sessions = self.session_manager._clean_inactive_sessions()
            for session in removed_sessions:
                if session.workspace.instance_id:
                    self.instance_manager.remove_instance(session.workspace.instance_id)
                    logger.info(f"Removing inactive Instance {session.workspace.instance_id}")
