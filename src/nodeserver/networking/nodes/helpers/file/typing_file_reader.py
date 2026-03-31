from __future__ import annotations
import json

from nodeserver.networking.nodes.data.custom_data_types import CustomSlotType
from nodeserver.networking.nodes.data.node_data import NodeData
from nodeserver.networking.nodes.data.node_data_types import BaseSlotType
from nodeserver.networking.nodes.helpers.file.node_scene_dataclasses import SceneData
from nodeserver.networking.nodes.helpers.file.type_dataclasses import NodeTypeData, SlotTypeData, TypeFile
from nodeserver.networking.nodes.helpers.node_constructor import BaseMirrorConstructor, CustomMirrorConstructor

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
    
    def get_constructor(self, type_name: str) -> BaseMirrorConstructor | None:
        return self.node_constructors.get(type_name, None)


    def load_from_file(self, file_path: str):
        with open(file_path, "r") as file:
            json_data = json.load(file)
            self._load_json_data(json_data)


    def serialize_to_dict(self) -> dict:
        json_data: dict = {
            "id": self._node_types_id,
            "version": self._node_types_version,
            "slot_types": {},
            "node_types": {}
        }
        for type_name, slot_type in self.slot_types.items():
            whitelist: list[str] = []
            type_data = SlotTypeData(
                extends=slot_type._super_type.value,
                conn_whitelist=whitelist,
                default_data_type=slot_type.data_type.type_name
            ).__dict__

            json_data["slot_types"][type_name] = type_data

        
        for type_name, constructor in self.node_constructors.items():
            parameters = {}

            for param_name, param in constructor._data_model.param_model.items():
                parameters[param_name] = {
                    "type": param.type
                }
                if param.range:
                    parameters[param_name]["range"] = param.range

            type_data = NodeTypeData(
                parameters=parameters,
                slots=constructor.slots
            ).__dict__
            json_data["node_types"][type_name] = type_data
        
        return json_data
        

    def _load_json_data(self, json_data: dict):
        type_data, slot_types, constructors = TypeFileReader._parse_json_data(json_data)
        
        self._raw_data = json_data

        self._node_types_id = type_data.id
        self._node_types_version = type_data.version
        
        self.slot_types = slot_types
        self.node_constructors = constructors
    

    @staticmethod
    def _parse_json_data(json_data: dict) -> tuple[TypeFile, dict[str, BaseSlotType], dict[str, BaseMirrorConstructor]]:
        type_data: TypeFile = TypeFile.from_dict(json_data)
        
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
                slot_types,
                node_type_data.slots,
            )
            constructors[type_name] = constructor
    
        return type_data, slot_types, constructors