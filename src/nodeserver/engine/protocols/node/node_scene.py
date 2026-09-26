from typing import Optional

from nodeserver.engine.helpers.node_instance_factory import NodeInstanceFactory
from nodeserver.engine.protocols.graph.scene_graph import SceneGraph
from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.engine.protocols.node.node_instance import NodeInstance
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.helpers.uuid_utils import IDGenerator
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData


class NodeScene:
    # TODO: add scene metadata like name, description, modified timestamps, etc
    scene_id: str

    registry: TypeRegistry
    graph: SceneGraph

    _logic_nodes: dict[str, BaseNode] # TODO?: talvez fazer um submanager para isso
    _factory: NodeInstanceFactory

    def __init__(self, registry: TypeRegistry, factory: Optional[NodeInstanceFactory] = None):
        self.scene_id = str(IDGenerator.generate_generic_id())
        self.graph = SceneGraph(registry)
        self._logic_nodes = {}
        
        self.registry = registry
        self._factory = factory or NodeInstanceFactory(self.registry)


    # TODO: talvez passar só a posição do node, etc.
    # para certificar de que os parâmetros vão ser definidos corretamente
    def create_node(self, node_fqn: str, node_scene_data: Optional[NodeSceneData] = None) -> NodeInstance:
        node_instance, logic_node = self._factory.create(node_fqn, node_scene_data)
        
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
