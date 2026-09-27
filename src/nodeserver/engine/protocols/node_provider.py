from typing import Optional, Protocol

from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.engine.protocols.node.node_instance import NodeInstance
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData


class INodeProvider(Protocol):
    def create_node(
        self, 
        node_type_fqn: str, 
        node_scene_data: Optional[NodeSceneData]
    ) -> tuple[NodeInstance, BaseNode]:
        raise NotImplementedError()
