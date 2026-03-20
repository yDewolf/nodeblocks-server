from nodeserver.networking.nodes.data.node_data_types import BaseNodeType, BaseSlotType
from nodeserver.networking.nodes.data.slot_data import SlotData
from nodeserver.networking.nodes.node.base_nodes import NodeMirror


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