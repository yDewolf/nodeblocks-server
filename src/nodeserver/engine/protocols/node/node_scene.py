from typing import Optional

from nodeserver.engine.protocols.graph.scene_graph import SceneGraph
from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.engine.protocols.node.node_instance import NodeInstance
from nodeserver.engine.protocols.providers.node_provider import INodeProvider
from nodeserver.engine.protocols.providers.scene_provider import ISceneDataProvider
from nodeserver.engine.protocols.providers.scene_state_provider import ISceneStateProvider
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.helpers.uuid_utils import IDGenerator
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData, SceneData
from nodeserver.protocols.manifest.package_manifest import ManifestPackage


class NodeScene:
    # TODO: add scene metadata like name, description, modified timestamps, etc
    scene_id: str
    graph: SceneGraph
    _logic_nodes: dict[str, BaseNode] # TODO?: talvez fazer um submanager para isso

    registry: TypeRegistry

    node_provider: INodeProvider
    scene_data_provider: ISceneDataProvider
    state_provider: ISceneStateProvider

    def __init__(self, registry: TypeRegistry, node_provider: INodeProvider, scene_data_provider: ISceneDataProvider, scene_state_provider: ISceneStateProvider, id: Optional[str] = None):
        self.registry = registry
        self.node_provider = node_provider
        self.scene_data_provider = scene_data_provider
        self.state_provider = scene_state_provider

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

    def delete_node(self, node_id: str) -> bool:
        removed: bool = self.graph.remove_node(node_id)
        self._logic_nodes.pop(node_id)
        return removed


    # Getters

    def get_logic_node(self, node_id: str) -> Optional[BaseNode]:
        return self._logic_nodes.get(node_id)


    # Overrides current scene by default
    def load_from_scene_data(self, scene_data: SceneData, override: bool = True):
        self.scene_data_provider.validate_scene_data(scene_data)
        if override:
            self.graph.reset_graph()

        for node_id, data in scene_data.nodes.items():
            self.create_node(data.nodetype_fqn, data)

        for conn_id, data in scene_data.connections.items():
            self.graph.add_connection(data)

    
    def as_scene_data(self) -> SceneData:
        self.state_provider._setup_folder()
        node_dependencies: set[tuple[str, str]] = set()
        for uid, node in self._logic_nodes.items():
            node_dependencies.union(
                self.node_provider.extract_node_dependencies(node)
            )
        
        return SceneData(
            uid=self.scene_id,
            dependencies={
                package_id: version for (package_id, version) in node_dependencies
            },
            nodes=self.graph.get_nodes_as_data(),
            connections=self.graph.get_conns_as_data()
        )
    
    def save_state(self):
        for uid, node in self._logic_nodes.items():
            logic_state = node.save_state(self.state_provider)
            if logic_state:
                self.state_provider._save_node_state(uid, logic_state)

        self.scene_data_provider.save_scene_data(
            self.as_scene_data()
        )
    
    def load_saved_state(self):
        scene_data = self.scene_data_provider.load_scene_data(self.scene_id)
        if not scene_data:
            return

        self.load_from_scene_data(scene_data, override=True)
        for uid, node in self._logic_nodes.items():
            node_state = self.state_provider._load_node_state(uid)
            if node_state: node.load_state(node_state)

