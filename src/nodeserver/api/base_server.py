import asyncio

from aiohttp import web

from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.web.rest.workspace.workspace_api import FileHandler
from nodeserver.api.websocket_manager import WebsocketManager
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import TypeFileReader

class NodeServer:
    instance_manager: InstanceManager
    websocket_manager: WebsocketManager

    file_handler: FileHandler

    host: str
    port: int
    app: web.Application

    def __init__(self, default_types: TypeFileReader | None = None, host="localhost", port=3001) -> None:
        self.app = web.Application()
        
        self.host = host
        self.port = port
        
        self.file_handler = FileHandler()

        self.instance_manager = InstanceManager(default_types)
        self.websocket_manager = WebsocketManager(self.instance_manager, host, port)
        self._setup_routes()

    def _setup_routes(self):
        # self.app.router.add_get('/api/{user_id}/files', self.file_handler.list_files)
        # self.app.router.add_post('/api/{user_id}/upload', self.file_handler.upload)
        
        self.app.router.add_get('/instance/{user_id}', self.handle_websocket)

    async def handle_websocket(self, request):
        if not self.websocket_manager.loop:
            self.websocket_manager.set_loop(asyncio.get_running_loop())
        
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        await self.websocket_manager.handle_connection(ws, request)

        return ws


    def run_server(self):
        web.run_app(self.app, host=self.host, port=self.port)