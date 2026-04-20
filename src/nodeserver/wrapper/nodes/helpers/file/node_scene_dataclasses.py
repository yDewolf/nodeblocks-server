import re
import uuid
from typing import Annotated, Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

class Vector2(BaseModel):
    x: float = 0.0
    y: float = 0.0
    
    @classmethod
    def from_dict(cls, data: dict, **kwargs):
        return cls.model_validate({**data, **kwargs})

class NodePathData(BaseModel):
    node_id: str = ""
    slot_name: str = ""

    @classmethod
    def from_str(cls, path: str) -> 'NodePathData':
        pattern = r"nodes:([a-z0-9-]+):slots:([^:\s]+)"
        match = re.search(pattern, path, re.IGNORECASE)
        if match:
            return cls(node_id=match.group(1), slot_name=match.group(2))
        return cls()

    def serialize(self) -> str:
        return self.make_path(self.node_id, self.slot_name)

    @staticmethod
    def make_path(node_id: str, slot_id: str) -> str:
        return f"nodes:{node_id}:slots:{slot_id}"
    
    @classmethod
    def from_dict(cls, data: dict, **kwargs):
        return cls.model_validate({**data, **kwargs})

NodePathSerialized = Annotated[
    NodePathData, 
    PlainSerializer(lambda path: path.serialize(), return_type=str)
]

class NodeSceneData(BaseModel):
    uid: Optional[str] = None
    type: str = ""
    position: Vector2
    data: Dict[str, Any] = Field(default_factory=dict)

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)
    
    @classmethod
    def from_dict(cls, data: dict, **kwargs):
        return cls.model_validate({**data, **kwargs})

class ConnectionSceneData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uid: Optional[str] = None
    from_slot: NodePathSerialized
    to_slot: NodePathSerialized

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)
    
    @classmethod
    def from_dict(cls, data: dict, **kwargs):
        return cls.model_validate({**data, **kwargs})
    
    @field_validator("from_slot", "to_slot", mode="before")
    @classmethod
    def parse_path_string(cls, value: Any) -> Any:
        if isinstance(value, str):
            return NodePathData.from_str(value)
        
        return value

class SceneData(BaseModel):
    uid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_types_id: str = "unknown"
    node_types_version: int = 0
    nodes: Dict[str, NodeSceneData] = Field(default_factory=dict)
    connections: Dict[str, ConnectionSceneData] = Field(default_factory=dict)

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)
    
    @classmethod
    def from_dict(cls, data: dict, **kwargs):
        return cls.model_validate({**data, **kwargs})