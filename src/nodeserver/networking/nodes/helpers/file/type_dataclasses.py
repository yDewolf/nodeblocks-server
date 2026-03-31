
from dataclasses import dataclass
from typing import Optional


@dataclass
class SlotTypeData:
    extends: str
    conn_whitelist: list[str]
    default_data_type: str

    @classmethod
    def from_dict(cls, data: dict) -> 'SlotTypeData':
        return cls(**data)

    def serialize(self) -> dict:
        return {
            "extends": self.extends,
            "conn_whitelist": self.conn_whitelist,
            "default_data_type": self.default_data_type
        }

@dataclass
class SlotData:
    type: str
    data_type: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> 'SlotData':
        return cls(
            type=data.get("type", ""),
            data_type=data.get("data_type")
        )

    def serialize(self) -> dict:
        return {
            "type": self.type,
            "data_type": self.data_type
        }

@dataclass
class NodeParameterData:
    type: str
    range: Optional[list[float | int]]

    @classmethod
    def from_dict(cls, data: dict) -> 'NodeParameterData':
        return cls(
            type=data.get("type", ""),
            range=data.get("range")
        )

    def serialize(self) -> dict:
        return {
            "type": self.type,
            "range": self.range
        }


@dataclass
class NodeTypeData:
    parameters: dict[str, NodeParameterData]
    slots: dict[str, SlotData]

    @classmethod
    def from_dict(cls, data: dict) -> 'NodeTypeData':
        params = {
            key: NodeParameterData.from_dict(value) 
            for key, value in data.get("parameters", {}).items()
        }
        slots = {
            key: SlotData.from_dict(value) 
            for key, value in data.get("slots", {}).items()
        }
        return cls(parameters=params, slots=slots)

    def serialize(self) -> dict:
        return {
            "parameters": {key: param.serialize() for key, param in self.parameters.items()},
            "slots": {key: slot.serialize() for key, slot in self.slots.items()}
        }


@dataclass
class TypeFile:
    version: int
    id: str
    slot_types: dict[str, SlotTypeData]
    node_types: dict[str, NodeTypeData]

    @classmethod
    def from_dict(cls, data: dict) -> 'TypeFile':
        # Orquestra a criação de toda a árvore de objetos
        slots = {
            k: SlotTypeData.from_dict(v) 
            for k, v in data.get("slot_types", {}).items()
        }
        nodes = {
            k: NodeTypeData.from_dict(v) 
            for k, v in data.get("node_types", {}).items()
        }
        
        return cls(
            version=data.get("version", -1),
            id=data.get("id", "unknown"),
            slot_types=slots,
            node_types=nodes
        )

    def serialize(self) -> dict:
        return {
            "version": self.version,
            "id": self.id,
            "slot_types": {key: slot_type.serialize() for key, slot_type in self.slot_types.items()},
            "node_types": {key: node_type.serialize() for key, node_type in self.node_types.items()}
        }
