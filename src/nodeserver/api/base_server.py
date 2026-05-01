import asyncio
from asyncio.log import logger
import logging

from aiohttp import web
import aiohttp_cors

from nodeserver.api.instance.server_instance import ServerInstance
from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.web.manager.session_manager import SessionManager
from nodeserver.api.web.rest.workspace.workspace_api import FileHandler
from nodeserver.api.websocket_manager import WebsocketManager
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import TypeFileReader

class NodeServer:
    instance_manager: InstanceManager
    websocket_manager: WebsocketManager
    session_manager: SessionManager

    file_handler: FileHandler

    host: str
    port: int
    app: web.Application

    def __init__(self, default_types: TypeFileReader | None = None, server_instance_type: type[ServerInstance] = ServerInstance, host="localhost", port=3001) -> None:
        self.app = web.Application()
        logging.basicConfig(level=logging.DEBUG)
        
        self.host = host
        self.port = port
        
        self.session_manager = SessionManager()
        self.file_handler = FileHandler(self.session_manager)

        self.instance_manager = InstanceManager(default_types)
        self.websocket_manager = WebsocketManager(self.instance_manager, self.session_manager, server_instance_type, host, port)
        self._setup_routes()

    def _setup_routes(self):
        cors = aiohttp_cors.setup(self.app, defaults={
            f"http://{self.host}:3000": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        })
        resource_files = cors.add(self.app.router.add_get('/api/{user_id}/files', self.file_handler.list_files))
        cors.add(self.app.router.add_get('/api/{user_id}/file/delete', self.file_handler.delete_file), {
            f"http://{self.host}:3000": aiohttp_cors.ResourceOptions(allow_credentials=True)
        })
        cors.add(self.app.router.add_get('/api/{user_id}/file/download', self.file_handler.download_file))
        cors.add(self.app.router.add_post('/api/{user_id}/file/upload', self.file_handler.upload_file),{
            f"http://{self.host}:3000": aiohttp_cors.ResourceOptions(
                allow_methods=("POST", "OPTIONS")
            )
        })
        # self.app.router.add_post('/api/{user_id}/upload', self.file_handler.upload)
        
        self.app.router.add_get('/ws/instance/{user_id}', self.handle_websocket)

    def run_server(self):
        web.run_app(self.app, host=self.host, port=self.port)


    async def handle_websocket(self, request):
        if not self.websocket_manager.loop:
            self.websocket_manager.set_loop(asyncio.get_running_loop())
            asyncio.create_task(self._clean_sessions_task()) # FIXME: move this somewhere else
        
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        await self.websocket_manager.handle_connection(ws, request)

        return ws

    
    async def _clean_sessions_task(self):
        while True:
            await asyncio.sleep(3.0)

            removed_sessions = self.session_manager._clean_inactive_sessions()
            for session in removed_sessions:
                if session.workspace.instance_id:
                    self.instance_manager.remove_instance(session.workspace.instance_id)
                    logger.info(f"Removing inactive Instance {session.workspace.instance_id}")
    