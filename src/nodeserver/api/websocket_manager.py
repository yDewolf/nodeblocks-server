import asyncio
from aiohttp import web

from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.internal.metadata_manager import MetadataManager
from nodeserver.api.web.instance.special_instance import WsServerInstance
from nodeserver.api.web.manager.session_manager import SessionManager
from nodeserver.api.web.manager.websocket_handler import WebsocketHandler
from nodeserver.api.instance.server_instance import ServerInstance
from nodeserver.api.web.message_router import BaseMessagerouter
import logging

from nodeserver.api.web.requests.websocket_requests import SrvMetadataUpdated

logger = logging.getLogger("nds.websocket")

class WebsocketManager:
    loop: asyncio.AbstractEventLoop | None = None
    host: str
    port: int

    handler: WebsocketHandler
    instance_manager: InstanceManager
    metadata_manager: MetadataManager

    stop: asyncio.Future | None

    def __init__(self, instance_manager: InstanceManager, metadata_manager: MetadataManager, session_manager: SessionManager, server_intance_type: type[WsServerInstance], host: str, port: int):
        self.instance_manager = instance_manager
        self.metadata_manager = metadata_manager
        self.handler = WebsocketHandler(self.instance_manager, session_manager, server_intance_type, BaseMessagerouter)

        self.host = host
        self.port = port

    async def handle_connection(self, ws: web.WebSocketResponse, request: web.Request):
        await self.handler.main_router(ws, request)

        return ws

    def sync_metadata_with_sockets(self, types_updated: list[str]):
        instances_by_type_id: dict[str, list[ServerInstance]] = {}
        for instance in self.instance_manager.get_all_instances():
            types_id = instance.mirror_manager.type_reader._node_types_id
            if types_id:
                if not instances_by_type_id.__contains__(types_id): 
                    instances_by_type_id[types_id] = []

                instances_by_type_id[types_id].append(instance)

        for type_id in types_updated:
            logger.info(f"Sending Metadata Updated to sockets related to type: {type_id}")
            instances = instances_by_type_id.get(type_id, [])
            meta_version = self.metadata_manager.get_metadata_version(type_id)
            for instance in instances:
                instance.send_to_client(SrvMetadataUpdated(
                    metadata_version=meta_version
                ))

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.handler.loop = self.loop
