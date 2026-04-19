from __future__ import annotations
from typing import Optional

from nodeserver.wrapper.nodes.data.node_data import NodeData
from nodeserver.wrapper.nodes.data.node_data_types import BaseNodeType, BaseSlotType, DataTypeUtils
from nodeserver.wrapper.nodes.helpers.file.node_scene_dataclasses import ConnectionSceneData, NodePathData
from nodeserver.wrapper.nodes.node.node_types import SuperSlotTypes
from nodeserver.wrapper.utils.uuid_utils import IDGenerator
from nodeserver.wrapper.nodes.helpers.file.node_scene_dataclasses import Vector2

class NodeMirror:
    uid: str
    node_name: str
    type_name: str    

    data: NodeData
    raw_data: dict
    _position: Optional[Vector2]

    slots: dict[SuperSlotTypes, list[SlotMirror]]

    def __init__(self, node_name: str, node_data: NodeData, uid: str | None = None, type_name: str = "BaseNode", _position: Vector2 | None = None):
        self.uid = uid if uid != None else IDGenerator.generate_node_id()
        self.node_name = node_name
        self.type_name = type_name
        self._position = _position

        self.data = node_data
        self.slots = {}

    def add_slot(self, slot_mirror: SlotMirror):
        if self.slots.get(slot_mirror.type._super_type) == None:
            self.slots[slot_mirror.type._super_type] = []
        
        self.slots[slot_mirror.type._super_type].append(slot_mirror)
    

    def get_slot(self, slot_name: str) -> SlotMirror | None:
        for super_type, slots in self.slots.items():
            for slot in slots:
                if slot.slot_name == slot_name:
                    return slot
        
        return None


class SlotMirror:
    slot_name: str
    parent_node: NodeMirror

    data_type: BaseNodeType
    type: BaseSlotType

    connections: dict[SlotMirror, ConnectionMirror]

    def __init__(self, parent_node: NodeMirror, slot_name: str, slot_type: BaseSlotType, slot_data_type: BaseNodeType | None) -> None:
        self.parent_node = parent_node
        self.slot_name = slot_name

        self.type = slot_type
        self.data_type = slot_data_type if slot_data_type != None else slot_type.data_type
        self.connections = {}

    def can_connect_to(self, slot: SlotMirror) -> bool:
        if slot == self:
            return False
        
        if not DataTypeUtils.is_type_compatible_with(self.data_type, slot.data_type):
            return False

        if not DataTypeUtils.is_type_compatible_with(self.type, slot.type):
            return False
    
        return True
    

    def add_conection(self, connection: ConnectionMirror):
        self.connections[connection.get_other_slot(self)] = connection
    
    def remove_connection(self, connection: ConnectionMirror):
        self.connections.pop(connection.get_other_slot(self))


class ConnectionMirror:
    uid: str
    slot_a: SlotMirror
    slot_b: SlotMirror

    def __init__(self, slot_a: SlotMirror, slot_b: SlotMirror, uid: str | None = None) -> None:
        self.uid = uid if uid != None else IDGenerator.generate_conn_id()
        self.slot_a = slot_a
        self.slot_b = slot_b

    def get_other_slot(self, root_slot: SlotMirror):
        if root_slot == self.slot_a:
            return self.slot_b
        
        if root_slot == self.slot_b:
            return self.slot_a
        
        return root_slot
    
    
    def connect(self):
        self.slot_a.add_conection(self)
        self.slot_b.add_conection(self)

    def disconnect(self):
        self.slot_a.remove_connection(self)
        self.slot_b.remove_connection(self)


    def get_input(self):
        if self.slot_a.type._super_type == SuperSlotTypes.INPUT:
            return self.slot_a
        
        return self.slot_b
    
    def get_output(self):
        if self.slot_a.type._super_type == SuperSlotTypes.OUTPUT:
            return self.slot_a
        
        return self.slot_b
    

    # TODO: do some checks I guess
    def is_valid(self) -> bool:
        if not self.slot_a.can_connect_to(self.slot_b):
            return False
        
        return True
    
    def to_scene_data(self) -> ConnectionSceneData:
        return ConnectionSceneData.from_dict({
            "uid": self.uid,
            "from": NodePathData(node_id=self.get_input().parent_node.uid, slot_name=self.get_input().slot_name),
            "to": NodePathData(node_id=self.get_output().parent_node.uid, slot_name=self.get_output().slot_name)
        })
        