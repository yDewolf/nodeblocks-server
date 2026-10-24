
from aiohttp import web

from nodeserver.server.web.app import NodeServerWebApp
from nodeserver.server.web.routing.base_router import BaseRouter


class PluginHTTPRouter(BaseRouter):
    def __init__(self, app: NodeServerWebApp) -> None:
        super().__init__(app)

    def _setup_routes(self):
        self.app.router.add_get("/api/plugins", self.get_plugin_list)
        self.app.router.add_get("/api/plugins/manifests", self.get_plugin_manifests)
    
    async def get_plugin_list(self, request: web.Request):
        installed_plugins = self.app.plugin_manager.get_installed_plugins()
        return web.json_response({
            "installed_plugins": [
                plugin_manifest.model_dump(
                    exclude={"node_modules", "data_types", "nodes_cache"}
                ) for plugin_manifest in installed_plugins.values()
            ]
        })

    async def get_plugin_manifests(self, request: web.Request):
        manifests = self.app.plugin_manager.get_all_loaded_packages()
        return web.json_response({
            "loaded_manifests": [
                manifest.serialize() for manifest in manifests.values()
            ]
        })
