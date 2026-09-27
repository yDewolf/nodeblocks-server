from typing import Optional, Protocol

from nodeserver.engine.helpers.node_instance_factory import NodeInstanceFactory
from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.engine.protocols.node.node_instance import NodeInstance
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData


class INodeProvider(Protocol):
    def create_node(
        self, 
        node_type_fqn: str, 
        node_scene_data: Optional[NodeSceneData]
    ) -> tuple[NodeInstance, BaseNode]:
        raise NotImplementedError()

# FIXME: não sei se vou manter isso aqui
class BaseNodeProvider(INodeProvider):
    registry: TypeRegistry
    factory: NodeInstanceFactory

    def __init__(self, registry: TypeRegistry, factory: Optional[NodeInstanceFactory] = None) -> None:
        super().__init__()
        self.registry = registry
        self.factory = factory or NodeInstanceFactory(registry)
    
    def create_node(self, node_type_fqn: str, node_scene_data: NodeSceneData | None) -> tuple[NodeInstance, BaseNode]:
        return self.factory.create(node_type_fqn, node_scene_data)
