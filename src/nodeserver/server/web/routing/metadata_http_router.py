from aiohttp import web

from nodeserver.server.web.app import NodeServerWebApp
from nodeserver.server.web.routing.base_router import BaseRouter


class MetadataHTTPRouter(BaseRouter):
    def __init__(self, app: NodeServerWebApp) -> None:
        super().__init__(app)

    def _setup_routes(self):
        self.app.router.add_get("/api/plugins/{package_id}/metadata", self.get_plugin_metadata)
        self.app.router.add_get("/api/plugins/{package_id}/metadata/header", self.get_plugin_metadata_header)
        self.app.router.add_get("/api/plugins/{package_id}/metadata/nodetypes", self.get_plugin_nodetypes_meta)
        self.app.router.add_get("/api/plugins/{package_id}/metadata/datatypes", self.get_plugin_datatypes_meta)
    
    async def get_plugin_metadata(self, request: web.Request):
        package_id = request.match_info["package_id"]
        if not self.app.metadata_provider.package_has_metadata(package_id):
            return web.HTTPNotFound()
        
        metadata = self.app.metadata_provider.get_metadata_manifest(package_id)
        return web.json_response(metadata.model_dump(mode="json"))


    async def get_plugin_metadata_header(self, request: web.Request):
        package_id = request.match_info["package_id"]
        if not self.app.metadata_provider.package_has_metadata(package_id):
            return web.HTTPNotFound()
        
        manifest = self.app.metadata_provider.get_metadata_header(package_id)
        return web.json_response(manifest.model_dump(mode="json"))


    async def get_plugin_nodetypes_meta(self, request: web.Request):
        package_id = request.match_info["package_id"]
        if not self.app.metadata_provider.package_has_metadata(package_id):
            return web.HTTPNotFound()
        
        node_id = request.query.get("node_id", None)
        node_types = self.app.metadata_provider.get_metadata_nodetypes(package_id)

        if node_id:
            if not node_id in node_types:
                return web.HTTPNotFound()

            return web.json_response(node_types[node_id].model_dump(mode="json"))

        return web.json_response({
            id: metadata.model_dump(mode="json") 
            for id, metadata in node_types.items() 
        })

    async def get_plugin_datatypes_meta(self, request: web.Request):
        package_id = request.match_info["package_id"]
        if not self.app.metadata_provider.package_has_metadata(package_id):
            return web.HTTPNotFound()
        
        datatype_id = request.query.get("datatype_id", None)
        datatypes = self.app.metadata_provider.get_metadata_datatypes(package_id)

        if datatype_id:
            if not datatype_id in datatypes:
                return web.HTTPNotFound()

            return web.json_response(datatypes[datatype_id].model_dump(mode="json"))

        return web.json_response({
            id: metadata.model_dump(mode="json") 
            for id, metadata in datatypes.items() 
        })

