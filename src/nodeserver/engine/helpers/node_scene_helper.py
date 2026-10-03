from typing import Optional

from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.protocols.node_provider import INodeProvider
from nodeserver.engine.protocols.scene_provider import ISceneDataProvider
from nodeserver.engine.protocols.scene_state_provider import ISceneStateProvider
from nodeserver.protocols.manifest.node.node_graph import SceneData


class NodeSceneHelper:
    @staticmethod
    def create_new_scene(plugin_manager: PluginManager, node_provider: INodeProvider, scene_data_provider: ISceneDataProvider, state_provider: ISceneStateProvider, scene_data: Optional[SceneData] = None, scene_id: Optional[str] = None):
        node_scene = NodeScene(plugin_manager.registry, node_provider, scene_data_provider, state_provider, id=scene_id)
        if scene_data:
            plugin_manager.version_manager.validate_scene_dependencies(
                scene_data.uid, scene_data.dependencies, plugin_manager.get_all_loaded_packages()
            )

            node_scene.load_from_scene_data(scene_data)
        
        return node_scene
