from typing import Optional

from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.protocols.node_provider import INodeProvider
from nodeserver.protocols.manifest.node.node_graph import SceneData


class NodeSceneHelper:
    @staticmethod
    def create_new_scene(plugin_manager: PluginManager, node_provider: INodeProvider, scene_data: Optional[SceneData] = None):
        node_scene = NodeScene(plugin_manager.registry, node_provider)
        if scene_data:
            plugin_manifest = plugin_manager.ensure_plugin_manifest(scene_data.package_id)
            plugin_manager.version_manager.validate_plugin_version(
                scene_data.package_version, plugin_manifest, plugin_id=scene_data.uid
            )

            node_scene.load_from_scene_data(scene_data)
        
        return node_scene
