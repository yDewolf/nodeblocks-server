
from nodeserver.networking.nodes.data.node_data import NodeData
from nodeserver.networking.nodes.node.node_slot import SlotMirror
from nodeserver.networking.nodes.node.node_types import SuperSlotTypes


class NodeMirror:
    id: int
    node_name: str
    type_name: str    

    raw_data: dict

    slots: dict[SuperSlotTypes, SlotMirror]

    def __init__(self, node_name: str, node_data: NodeData, id: int = -1, type_name: str = "BaseNode"):
        self.id = id
        self.node_name = node_name

        self.type_name = type_name
    