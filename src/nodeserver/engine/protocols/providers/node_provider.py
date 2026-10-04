from abc import abstractmethod
from typing import Optional, Protocol

from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.engine.protocols.node.node_instance import NodeInstance
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData
from nodeserver.protocols.manifest.package_manifest import ManifestPackage


class INodeProvider(Protocol):
    @abstractmethod
    def create_node(
        self, 
        node_type_fqn: str, 
        node_scene_data: Optional[NodeSceneData]
    ) -> tuple[NodeInstance, BaseNode]:
        pass

    @abstractmethod
    def extract_node_dependencies(self, node: BaseNode) -> set[ManifestPackage]:
        pass
        
