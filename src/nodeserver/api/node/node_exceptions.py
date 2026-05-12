from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror


class NoOutputException(Exception):
    pass

class ConnRecursionException(Exception):
    problematic_nodes: list[NodeMirror]
    def __init__(self, cyclic_nodes: list[NodeMirror], *args: object) -> None:
        super().__init__(*args)
        self.problematic_nodes = cyclic_nodes