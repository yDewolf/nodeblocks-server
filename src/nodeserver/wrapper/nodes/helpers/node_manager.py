
from typing import Optional
from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror


class NodeMirrorManager:
    _nodes: dict[str, NodeMirror]
    
    def __init__(self) -> None:
        self._nodes = {}

    def clear(self):
        self._nodes.clear()

    
    def get_node(self, uid: str):
        return self._nodes.get(uid)


    def add_node(self, node_mirror: NodeMirror):
        # TODO: Check for duplicate ids and other
        self._nodes[node_mirror.uid] = node_mirror

    def remove_node(self, uid: str) -> Optional[NodeMirror]:
        if not self._nodes.__contains__(uid):
            return None
        
        node = self._nodes.pop(uid)
        return node