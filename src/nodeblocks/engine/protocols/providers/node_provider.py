from abc import abstractmethod
from typing import Optional, Protocol

from nodeblocks.engine.protocols.node.logic_nodes import BaseNode
from nodeblocks.engine.protocols.node.node_instance import NodeInstance
from nodeblocks.protocols.manifest.node.node_graph import NodeSceneData
from nodeblocks.protocols.manifest.package_manifest import ManifestPackage


class INodeProvider(Protocol):
    @abstractmethod
    def create_node(
        self, 
        node_type_fqn: str, 
        node_scene_data: Optional[NodeSceneData]
    ) -> tuple[NodeInstance, BaseNode]:
        pass

    # package_id, version
    @abstractmethod
    def extract_node_dependencies(self, node: BaseNode) -> set[tuple[str, str]]:
        pass
        
