
from nodeserver.networking.nodes.data.node_data import NodeData
from nodeserver.networking.nodes.data.node_data_types import  BaseNodeType, BaseSlotType, DataTypeUtils
from nodeserver.networking.nodes.data.slot_data import SlotData
from nodeserver.networking.nodes.node.base_nodes import NodeMirror, SlotMirror


class BaseNodeConstructor:
    type_name: str

    _data: NodeData
    _slots: dict[str, SlotData]
    _slot_types: dict[str, BaseSlotType]

    def __init__(self, type_name: str) -> None:
        self.type_name = type_name

        self._data = NodeData({})
        self.slots = {}
        self._slot_types = {}
    
    def make_node_mirror(self, node_name: str, id: int) -> NodeMirror | None:
        mirror = NodeMirror(node_name, self._data, id, self.type_name)
        for slot_name in self._slots:
            slot_data = self._slots[slot_name]
            new_slot = self.make_slot_mirror(mirror, slot_name, slot_data)
            if not new_slot:
                return None

            mirror.slots[new_slot.type._super_type] = new_slot
        
        return mirror


    def make_slot_mirror(self, parent_node: NodeMirror, slot_name: str, slot_data: SlotData):
        slot_type_str = slot_data.type if slot_data.type != None else ""
        slot_type = self._slot_types.get(slot_type_str)
        if not slot_type:
            # Search for default slot types
            slot_type = DataTypeUtils._match_slot_type_str(slot_type_str)
            
            if slot_type == None:
                return None

        slot_data_type = DataTypeUtils._match_data_type_str(slot_data.data_type if slot_data.data_type != None else "")
        return SlotMirror(
            parent_node,
            slot_name,
            slot_type,
            slot_data_type
        )

class CustomNodeConstructor(BaseNodeConstructor):
    def __init__(self, type_name: str, data: NodeData, slots: dict[str, SlotData], slot_types: dict[str, BaseSlotType]) -> None:
        super().__init__(type_name)

        self._data = data
        self._slots = slots
        self._slot_types = slot_types