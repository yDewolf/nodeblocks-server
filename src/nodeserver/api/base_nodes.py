
from nodeserver.networking.nodes.node.base_nodes import NodeMirror


class BaseNode:
    _mirror: NodeMirror
    # TODO
    def __init__(self, mirror: NodeMirror | None = None):
        if mirror != None:
            self._mirror = mirror

    
    def forward(self, input):
        return input