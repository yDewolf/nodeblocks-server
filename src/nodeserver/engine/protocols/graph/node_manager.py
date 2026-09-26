from typing import Optional

from nodeserver.engine.protocols.node.node_instance import NodeInstance


class NodeManager:
    _nodes: dict[str, NodeInstance]
    
    @property
    def node_index(self): return self._nodes

    @property
    def node_instances(self): return self._nodes.values()
    @property
    def node_ids(self): return self._nodes.keys()

    def __init__(self) -> None:
        self._nodes = {}


    def add(self, node: NodeInstance) -> None:
        if node.uid in self._nodes:
            raise Exception(f"A node with the same UID already exists in node manager")
        self._nodes[node.uid] = node

    def remove(self, node_id: str) -> Optional[NodeInstance]:
        return self._nodes.pop(node_id, None)

    def get(self, node_id: str) -> Optional[NodeInstance]:
        return self._nodes.get(node_id)

    def all(self) -> dict[str, NodeInstance]:
        return self._nodes
