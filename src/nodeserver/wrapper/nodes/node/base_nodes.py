from __future__ import annotations
from abc import abstractmethod
from typing import Any, Optional

from nodeserver.api.node.node_exceptions import ReachedMaxConnections
from nodeserver.wrapper.nodes.data.node_data import NodeData
from nodeserver.wrapper.nodes.data.node_data_types import BaseDataType, DataTypeUtils
from nodeserver.wrapper.metadata.nodes.node_metadata import NodeTypeMeta
from nodeserver.wrapper.nodes.data.slot_types import BaseSlotType, SlotTypeUtils
from nodeserver.wrapper.nodes.helpers.file.node_scene_dataclasses import ConnectionSceneData, NodePathData
from nodeserver.wrapper.utils.uuid_utils import IDGenerator
from nodeserver.wrapper.nodes.helpers.file.node_scene_dataclasses import Vector2

class NodeMirror:
    uid: str
    node_name: str
    type_name: str    

    data: NodeData
    metadata: NodeTypeMeta
    raw_data: dict
    _position: Optional[Vector2]

    slots: list[SlotMirror]

    def __init__(self, node_name: str, node_data: NodeData, metadata: NodeTypeMeta, uid: str | None = None, type_name: str = "BaseNode", _position: Vector2 | None = None):
        self.uid = uid if uid != None else IDGenerator.generate_node_id()
        self.node_name = node_name
        self.type_name = type_name
        self._position = _position

        self.metadata = metadata
        self.data = node_data
        self.slots = []

    def add_slot(self, slot_mirror: SlotMirror):
        self.slots.append(slot_mirror)
    

    def get_slot(self, slot_name: str) -> SlotMirror | None:
        for slot in self.slots:
            if slot.slot_name == slot_name:
                return slot
        
        return None
    
    @property
    def inputs(self) -> list[SlotMirror]:
        inputs: list[SlotMirror] = []
        for slot in self.slots:
            if slot.is_input:
                inputs.append(slot)
        
        return inputs

    @property
    def outputs(self) -> list[SlotMirror]:
        outputs: list[SlotMirror] = []
        for slot in self.slots:
            if not slot.is_input:
                outputs.append(slot)
        
        return outputs

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.uid})"


class _ParsedNode:
    _mirror: NodeMirror

    def __init__(self, mirror: Optional[NodeMirror] = None) -> None:
        if mirror:
            self._mirror = mirror

    @abstractmethod
    def load_state(self, root_state_path: str, state: Any):
        pass
    
    @abstractmethod
    def save_state(self, root_state_path: str) -> Any:
        pass
    
    def has_mirror(self) -> bool:
        return hasattr(self, "_mirror")

class SlotMirror:
    _version: int

    slot_name: str
    parent_node: NodeMirror

    max_connections: int = 0
    data_type: BaseDataType

    _is_input: bool
    type: BaseSlotType

    connections: dict[SlotMirror, ConnectionMirror]

    def __init__(self, parent_node: NodeMirror, slot_name: str, slot_type: BaseSlotType, is_input: bool, max_connections: int = 0) -> None:
        self._version = 0
        self._is_input = is_input
        self.parent_node = parent_node
        self.slot_name = slot_name

        self.type = slot_type
        self.max_connections = max_connections
        self.connections = {}

    @property
    def is_input(self):
        return self._is_input

    def can_connect_to(self, slot: SlotMirror) -> bool:
        if slot == self:
            return False
        
        # if not DataTypeUtils.is_type_compatible_with(self.data_type, slot.data_type):
        #     return False
        if len(self.connections.values()) >= self.max_connections and self.max_connections != 0:
            raise ReachedMaxConnections(self) # type: ignore

        if not SlotTypeUtils.is_type_compatible_with(self.type, slot.type):
            return False
    
        return True
    

    def add_conection(self, connection: ConnectionMirror):
        self.connections[connection.get_other_slot(self)] = connection
        self._version += 1
    
    def remove_connection(self, connection: ConnectionMirror):
        self.connections.pop(connection.get_other_slot(self))
        self._version += 1


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
        if self.slot_a.is_input:
            return self.slot_a
        
        return self.slot_b
    
    def get_output(self):
        if not self.slot_a.is_input:
            return self.slot_a
        
        return self.slot_b
    

    # TODO: do some checks I guess
    def is_valid(self) -> bool:
        if not self.slot_a.can_connect_to(self.slot_b):
            return False
        
        if not self.slot_b.can_connect_to(self.slot_a):
            return False
        
        return True
    
    def to_scene_data(self) -> ConnectionSceneData:
        return ConnectionSceneData.from_dict({
            "uid": self.uid,
            "from": NodePathData(node_id=self.get_input().parent_node.uid, slot_name=self.get_input().slot_name),
            "to": NodePathData(node_id=self.get_output().parent_node.uid, slot_name=self.get_output().slot_name)
        })
        