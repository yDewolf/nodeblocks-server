import re
from typing import Annotated, Any, Dict
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer, field_validator

from nodeserver.protocols.helpers.uuid_utils import IDGenerator
from nodeserver.protocols.manifest.structs.scene_structs import Vector2

class NodePathData(BaseModel):
    node_id: str = ""
    slot_id: str = ""

    def serialize(self) -> str:
        return self.make_path(self.node_id, self.slot_id)

    @staticmethod
    def make_path(node_id: str, slot_id: str) -> str:
        return f"nodes:{node_id}:slots:{slot_id}"
    
    @classmethod
    def parse_path(cls, value: Any) -> "NodePathData":
        if isinstance(value, cls):
            return value

        if isinstance(value, str):
            pattern = r"nodes:([a-z0-9-]+):slots:([^:\s]+)"
            match = re.search(pattern, value, re.IGNORECASE)
            if match:
                return cls(node_id=match.group(1), slot_id=match.group(2))
        
        if isinstance(value, dict):
            return cls.model_validate(value)

        return cls()


NodePathSerialized = Annotated[
    NodePathData, 
    BeforeValidator(NodePathData.parse_path),
    PlainSerializer(lambda path: path.serialize(), return_type=str),
]

class NodeSceneData(BaseModel):
    uid: str = Field(default_factory=IDGenerator.generate_node_id)
    type_id: str
    position: Vector2 = Field(default=Vector2())
    data: Dict[str, Any] = Field(default_factory=dict)

class ConnectionSceneData(BaseModel):
    model_config = ConfigDict(validate_by_name=True)

    uid: str = Field(default_factory=IDGenerator.generate_conn_id)
    from_slot: NodePathSerialized
    to_slot: NodePathSerialized

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)


class SceneData(BaseModel):
    uid: str = Field(default_factory=IDGenerator.generate_generic_id)

    package_id: str = "unknown" # FIXME on client: node_types_id -> package_id
    # TODO: implement a better version control system
    package_version: int = 0 # FIXME on client: node_types_version -> package_version 

    nodes: Dict[str, NodeSceneData] = Field(default_factory=dict)
    connections: Dict[str, ConnectionSceneData] = Field(default_factory=dict)

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)
