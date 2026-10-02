from typing import Optional

from nodeserver.engine.helpers.node_instance_factory import NodeInstanceFactory
from nodeserver.engine.protocols.graph.scene_graph import SceneGraph
from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.engine.protocols.node.node_instance import NodeInstance
from nodeserver.engine.protocols.node_provider import INodeProvider
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.helpers.uuid_utils import IDGenerator
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData, SceneData


class NodeScene:
    # TODO: add scene metadata like name, description, modified timestamps, etc
    scene_id: str
    graph: SceneGraph
    _logic_nodes: dict[str, BaseNode] # TODO?: talvez fazer um submanager para isso

    registry: TypeRegistry
    node_provider: INodeProvider

    def __init__(self, registry: TypeRegistry, node_provider: INodeProvider, id: Optional[str] = None):
        self.registry = registry
        self.node_provider = node_provider

        self.scene_id = id or IDGenerator.generate_generic_id(length=6)
        self.graph = SceneGraph(registry)
        self._logic_nodes = {}


    # TODO: talvez passar só a posição do node, etc.
    # para certificar de que os parâmetros vão ser definidos corretamente
    def create_node(self, node_fqn: str, node_scene_data: Optional[NodeSceneData] = None) -> NodeInstance:
        node_instance, logic_node = self.node_provider.create_node(node_fqn, node_scene_data)
        
        self._logic_nodes[node_instance.uid] = logic_node
        self.graph.add_node(node_instance)
        
        return node_instance

    def delete_node(self, node_id: str):
        self.graph.remove_node(node_id)
        self._logic_nodes.pop(node_id)


    # Getters

    def get_logic_node(self, node_id: str) -> Optional[BaseNode]:
        return self._logic_nodes.get(node_id)


    # TODO: implement save and load (baseado em SceneData)
    
    # Overrides current scene by default
    # This assumes the provided scene is valid and is compatible with the current plugins etc
    def load_from_scene_data(self, scene_data: SceneData, override: bool = True):
        if override:
            self.graph.reset_graph()

        for node_id, data in scene_data.nodes.items():
            self.create_node(data.type_id, data)

        for conn_id, data in scene_data.connections.items():
            self.graph.add_connection(data)
        