


from nodeserver.api.internal.node_protocols import NodeMirrorProtocol, SlotMirrorProtocol


class NoOutputException(Exception):
    pass

class ReachedMaxConnections(Exception):
    slot: SlotMirrorProtocol
    def __init__(self, slot: SlotMirrorProtocol, *args: object) -> None:
        self.slot = slot
        super().__init__(*args)

class ConnRecursionException(Exception):
    problematic_nodes: list[NodeMirrorProtocol]
    def __init__(self, cyclic_nodes: list[NodeMirrorProtocol], *args: object) -> None:
        super().__init__(*args)
        self.problematic_nodes = cyclic_nodes
