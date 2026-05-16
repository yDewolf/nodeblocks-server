
from typing import Any, Callable
from nodeserver.wrapper.nodes.data.node_data import NodeData
from nodeserver.wrapper.nodes.data.node_data_types import  UNKNOWN_TYPE, BaseSlotType, DataTypeUtils
from nodeserver.wrapper.nodes.data.node_metadata import NodeMetadata
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import SlotData
from nodeserver.wrapper.nodes.helpers.file.node_scene_dataclasses import Vector2
from nodeserver.wrapper.nodes.node.base_nodes import _ParsedNode, NodeMirror, SlotMirror


def _default_build_func(mirror: NodeMirror) -> _ParsedNode:
    return _ParsedNode(mirror)

class BaseMirrorConstructor:
    type_name: str

    _data_model: NodeData
    _metadata: NodeMetadata
    _slots: dict[str, SlotData]
    _slot_types: dict[str, BaseSlotType]

    _builder_func: Callable[[NodeMirror], _ParsedNode]

    def __init__(self, type_name: str, metadata: NodeMetadata, builder_func: Callable[[NodeMirror], _ParsedNode] = _default_build_func) -> None:
        self.type_name = type_name
        self._metadata = metadata
        self._builder_func = builder_func

        self._data_model = NodeData({})
        self._slots = {}
        self._slot_types = {}
    
    def make_node_mirror(self, node_name: str, id: str, node_data: dict[str, Any], metadata: NodeMetadata, _position: Vector2) -> NodeMirror | None:
        mirror = NodeMirror(node_name, NodeData.from_model(self._data_model), metadata, id, self.type_name, _position)
        mirror.data.parse_parameters(node_data)

        for slot_name in self._slots:
            slot_data = self._slots[slot_name]
            new_slot = self.make_slot_mirror(mirror, slot_name, slot_data)
            if not new_slot:
                return None

            mirror.add_slot(new_slot)
        
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
            slot_data_type if slot_data_type != UNKNOWN_TYPE else None,
            slot_data.max_connections if slot_data.max_connections else 0
        )

    def build_node(self, mirror: NodeMirror) -> _ParsedNode:
        return self._builder_func(mirror)

class CustomMirrorConstructor(BaseMirrorConstructor):
    def __init__(self, type_name: str, data: NodeData, metadata: NodeMetadata, slot_types: dict[str, BaseSlotType], slots: dict[str, SlotData], builder_func: Callable[[NodeMirror], _ParsedNode] = _default_build_func) -> None:
        super().__init__(type_name, metadata, builder_func)

        self._data_model = data
        self._slots = slots
        self._slot_types = slot_types