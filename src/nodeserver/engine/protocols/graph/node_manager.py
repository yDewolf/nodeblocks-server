from typing import Optional

from nodeserver.engine.protocols.node_instance import NodeInstance


class NodeManager:
    _nodes: dict[str, NodeInstance]
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
