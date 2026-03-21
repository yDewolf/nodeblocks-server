from __future__ import annotations

from nodeserver.networking.nodes.data.node_data import NodeData
from nodeserver.networking.nodes.data.node_data_types import BaseNodeType, BaseSlotType
from nodeserver.networking.nodes.node.node_types import SuperSlotTypes

class NodeMirror:
    id: int
    node_name: str
    type_name: str    

    raw_data: dict

    slots: dict[SuperSlotTypes, SlotMirror]

    def __init__(self, node_name: str, node_data: NodeData, id: int = -1, type_name: str = "BaseNode"):
        self.id = id
        self.slots = {}
        self.node_name = node_name

        self.type_name = type_name

class SlotMirror:
    slot_name: str
    parent_node: NodeMirror

    data_type: BaseNodeType
    type: BaseSlotType

    def __init__(self, parent_node: NodeMirror, slot_name: str, slot_type: BaseSlotType, slot_data_type: BaseNodeType | None) -> None:
        self.parent_node = parent_node
        self.slot_name = slot_name

        self.type = slot_type
        self.data_type = slot_data_type if slot_data_type != None else slot_type.data_type
