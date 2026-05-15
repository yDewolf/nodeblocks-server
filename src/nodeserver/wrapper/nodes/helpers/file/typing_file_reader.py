from __future__ import annotations
from dataclasses import dataclass
import json
from typing import Callable, Optional

from nodeserver.wrapper.nodes.data.custom_data_types import CustomSlotType
from nodeserver.wrapper.nodes.data.node_data import NodeData
from nodeserver.wrapper.nodes.data.node_data_types import BaseSlotType
from nodeserver.wrapper.nodes.data.node_metadata import NodeMetadata
from nodeserver.wrapper.nodes.helpers.file.node_scene_dataclasses import SceneData
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import NodeTypeData, SlotData, SlotTypeData, TypeFile
from nodeserver.wrapper.nodes.helpers.node_constructor import BaseMirrorConstructor, CustomMirrorConstructor
from nodeserver.wrapper.nodes.node.base_nodes import _ParsedNode, NodeMirror

class TypeFileReader:
    _node_types_version: int = -1
    _node_types_id: str | None = None
    
    # file_path: str | None = None
    _raw_data: dict | None = None

    slot_types: dict[str, BaseSlotType]
    node_constructors: dict[str, BaseMirrorConstructor]

    def __init__(self) -> None:
        self.slot_types = {}
        self.node_constructors = {}

    @staticmethod
    def new(version: int, id: str, slot_types: dict[str, BaseSlotType], constructors: list[BaseMirrorConstructor]) -> TypeFileReader:
        types = TypeFileReader()
        types._node_types_version = version
        types._node_types_id = id

        types.slot_types = slot_types
        for constructor in constructors:
            types.set_constructor(constructor.type_name, constructor)

        return types

    # TODO:
    def save_to_file(self):
        pass


    def is_scene_compatible(self, scene_data: SceneData):
        if scene_data.node_types_id != self._node_types_id:
            return False
        
        if scene_data.node_types_version != self._node_types_version:
            return False
        
        has_missing_constructor = False
        for node_data in scene_data.nodes.values():
            if not self.node_constructors.__contains__(node_data.type):
                has_missing_constructor = True
                break
        
        if has_missing_constructor:
            return False
        
        return True


    def set_constructor(self, type_name: str, constructor: BaseMirrorConstructor):
        self.node_constructors[type_name] = constructor
    
    def set_new_constructors(self, constructors: list[BaseMirrorConstructor]):
        self.node_constructors.clear()
        for constructor in constructors:
            self.set_constructor(constructor.type_name, constructor)


    def get_constructor(self, type_name: str) -> BaseMirrorConstructor | None:
        return self.node_constructors.get(type_name, None)


    def load_from_file(self, file_path: str):
        with open(file_path, "r") as file:
            json_data = json.load(file)
            self._load_json_data(json_data)


    def serialize(self) -> TypeFile:
        _slot_types: dict[str, SlotTypeData] = {}
        for type_name, slot_type in self.slot_types.items():
            whitelist: list[str] = []
            for name in slot_type._name_whitelist: whitelist.append(name)
            for super_type in slot_type._type_whitelist: whitelist.append(f"#{super_type.value}")
            type_data = SlotTypeData(
                extends=slot_type._super_type.value,
                conn_whitelist=whitelist,
                default_data_type=slot_type.data_type.type_name
            )
            _slot_types[type_name] = type_data

        _node_types: dict[str, NodeTypeData] = {}
        for type_name, constructor in self.node_constructors.items():
            type_data = NodeTypeData(
                parameters=constructor._data_model.param_model,
                metadata=constructor._metadata,
                slots=constructor._slots
            )
            _node_types[type_name] = type_data
        
        type_data = TypeFile(
            id=self._node_types_id if self._node_types_id else "unknown",
            version=self._node_types_version,
            slot_types=_slot_types,
            node_types=_node_types
        )

        return type_data
        

    def _load_json_data(self, json_data: dict):
        type_data, slot_types, constructors = TypeFileReader._parse_json_data(json_data)
        
        self._raw_data = json_data

        self._node_types_id = type_data.id
        self._node_types_version = type_data.version
        
        self.slot_types = slot_types
        self.node_constructors = constructors
    

    @staticmethod
    def _parse_json_data(json_data: dict) -> tuple[TypeFile, dict[str, BaseSlotType], dict[str, BaseMirrorConstructor]]:
        type_data: TypeFile = TypeFile.model_validate(json_data)
        
        constructors: dict[str, BaseMirrorConstructor] = {}
        slot_types: dict[str, BaseSlotType] = {}

        for type_name in type_data.slot_types:
            slot_type_data = type_data.slot_types[type_name]
            custom_type = CustomSlotType(
                type_name,
                slot_type_data.default_data_type,
                slot_type_data.extends,
                slot_type_data.conn_whitelist
            )
            slot_types[type_name] = custom_type
        
        for type_name in type_data.node_types:
            node_type_data = type_data.node_types[type_name]
            constructor = CustomMirrorConstructor(
                type_name,
                NodeData(node_type_data.parameters),
                node_type_data.metadata,
                slot_types,
                node_type_data.slots
            )
            constructors[type_name] = constructor
    
        return type_data, slot_types, constructors

@dataclass
class ConstructorModel:
    type_name: str
    node_data: Optional[NodeData]
    node_metadata: Optional[NodeMetadata]

    slots: Optional[dict[str, SlotData]]
    parser: Optional[Callable[[NodeMirror], _ParsedNode]]

    @staticmethod
    def new(type_name: str, node_data: Optional[NodeData] = None, metadata: Optional[NodeMetadata] = None, slots: Optional[dict[str, SlotData]] = None, parser: Optional[Callable[[NodeMirror], _ParsedNode]] = None) -> 'ConstructorModel':
        return ConstructorModel(
            type_name=type_name,
            node_data=node_data,
            node_metadata=metadata,
            slots=slots,
            parser=parser,
        )