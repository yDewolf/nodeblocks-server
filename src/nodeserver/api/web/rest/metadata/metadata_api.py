
from enum import Enum
from typing import Optional

from aiohttp import web
import aiohttp_cors

from nodeserver.api.internal.metadata_manager import MetadataManager
from nodeserver.api.web.manager.session_manager import SessionManager
from nodeserver.api.web.rest.rest_utils import BaseRequestRouter, RestUtils
from nodeserver.wrapper.metadata.metadata_header import Metadata, MetadataFileHeader

class MetadataRequests(Enum):
    GET_HEADER = 0
    GET_NODE = 1
    GET_DATATYPE = 2

class MetadataHandler(BaseRequestRouter):
    metadata_manager: MetadataManager

    def __init__(self, metadata_manager: MetadataManager, session_manager: SessionManager) -> None:
        super().__init__(session_manager)
        self.metadata_manager = metadata_manager

    def setup_http_routes(self, app: web.Application, host: str, cors: aiohttp_cors.CorsConfig):
        cors.add(app.router.add_get("/api/metadata", self.meta_header))
        cors.add(app.router.add_get("/api/metadata/nodes", self.node_meta))
        cors.add(app.router.add_get("/api/metadata/datatypes", self.datatype_meta))
    

    async def route_request(self, request: web.Request, request_type: MetadataRequests) -> web.StreamResponse:
        user_session, error = RestUtils.get_session_from_request(self.session_manager, request)
        if error: return error
        if not user_session: return web.json_response({})
        
        instance = user_session.workspace.current_instance
        if not instance:
            return web.json_response({"message": "Couldn't find assigned instance for user session"})
        
        types_id = instance.mirror_manager.type_reader._node_types_id
        if not types_id:
            return web.json_response({"message": "Instance doesn't have any types loaded"})
        
        metadata = self.metadata_manager.get_metadata(types_id)
        if not metadata:
            return web.json_response({"message": f"Couldn't find metadata for type: {types_id}"})

        result = web.json_response({"message": "internal_error"}, status=400)
        match request_type:
            case MetadataRequests.GET_HEADER: 
                result = self.get_metadata_header(metadata)
            
            case MetadataRequests.GET_NODE:
                type_id = request.query.get("type_id")
                result = self.get_node_metadata(metadata, type_id)

            case MetadataRequests.GET_DATATYPE: 
                datatype_id = request.query.get("datatype_id")
                result = self.get_datatype_metadata(metadata, datatype_id)

        return result
    
    # Use these to as app.route handler
    async def meta_header(self, request: web.Request):
        return await self.route_request(request, MetadataRequests.GET_HEADER)

    async def node_meta(self, request: web.Request):
        return await self.route_request(request, MetadataRequests.GET_NODE)

    async def datatype_meta(self, request: web.Request):
        return await self.route_request(request, MetadataRequests.GET_DATATYPE)
    

    def get_metadata_header(self, metadata: Metadata) -> web.Response:
        header_data = MetadataFileHeader.model_validate(metadata).model_dump(mode="json")
        return web.json_response(header_data)

    def get_node_metadata(self, metadata: Metadata, type_id: Optional[str] = None) -> web.Response:
        node_types_data = metadata.node_types
        if type_id:
            node_meta = node_types_data.get(type_id)
            if not node_meta:
                return web.json_response({}, status=404)

            return web.json_response(node_meta.model_dump(mode="json"))

        raw_nodes = {key: node_type.model_dump(mode="json") for key, node_type in node_types_data.items()}
        return web.json_response(raw_nodes)

    def get_datatype_metadata(self, metadata: Metadata, datatype_id: Optional[str] = None) -> web.Response:
        data_types_data = metadata.data_types
        if datatype_id:
            node_meta = data_types_data.get(datatype_id)
            if not node_meta:
                return web.json_response({}, status=404)

            return web.json_response(node_meta.model_dump(mode="json"))

        raw_nodes = {key: node_type.model_dump(mode="json") for key, node_type in data_types_data.items()}
        return web.json_response(raw_nodes)
