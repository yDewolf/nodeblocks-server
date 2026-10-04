from nodeserver.engine.helpers.node_instance_factory import NodeInstanceFactory
from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.engine.protocols.node.node_instance import NodeInstance
from nodeserver.engine.protocols.providers.node_provider import INodeProvider
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData
from nodeserver.protocols.manifest.package_manifest import ManifestPackage


from typing import Optional


class BaseNodeProvider(INodeProvider):
    registry: TypeRegistry
    factory: NodeInstanceFactory

    def __init__(self, registry: TypeRegistry, factory: Optional[NodeInstanceFactory] = None) -> None:
        super().__init__()
        self.registry = registry
        self.factory = factory or NodeInstanceFactory(registry)

    def create_node(self, node_type_fqn: str, node_scene_data: NodeSceneData | None) -> tuple[NodeInstance, BaseNode]:
        return self.factory.create(node_type_fqn, node_scene_data)


    def extract_node_dependencies(self, node: BaseNode) -> set[ManifestPackage]:
        # TODO
        return set()
