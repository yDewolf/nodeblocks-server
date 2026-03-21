
from nodeserver.networking.nodes.node.base_nodes import NodeMirror


class NodeManager:
    _nodes: dict[int, NodeMirror]
    
    def __init__(self) -> None:
        self._nodes = {}

    def clear(self):
        self._nodes.clear()

    
    def get_node(self, id: int):
        return self._nodes.get(id)


    def add_node(self, node_mirror: NodeMirror):
        # TODO: Check for duplicate ids and other
        self._nodes[node_mirror.id] = node_mirror

    def remove_node(self, node_mirror: NodeMirror):
        # TODO: Use id to remove node
        self._nodes.pop(node_mirror.id)