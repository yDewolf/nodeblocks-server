
from nodeserver.networking.nodes.node.base_nodes import NodeMirror


class BaseNode:
    _mirror: NodeMirror

    # TODO
    def __init__(self):
        pass

    # TODO
    @staticmethod
    def from_mirror(mirror: NodeMirror):
        new_node = BaseNode()
        new_node._mirror = mirror

        return new_node

    
    def forward(self, input):
        return input