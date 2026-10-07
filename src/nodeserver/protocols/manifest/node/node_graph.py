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
    nodetype_fqn: str
    position: Vector2 = Field(default=Vector2())
    data: Dict[str, Any] = Field(default_factory=dict) # node parameters

class ConnectionSceneData(BaseModel):
    model_config = ConfigDict(validate_by_name=True)

    uid: str = Field(default_factory=IDGenerator.generate_conn_id)
    from_slot: NodePathSerialized
    to_slot: NodePathSerialized

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)

    @classmethod
    def from_ids(cls, from_node_id: str, from_slot_id: str, to_node_id: str, to_slot_id: str):
        return cls(
            from_slot=NodePathData(node_id=from_node_id, slot_id=from_slot_id),
            to_slot=NodePathData(node_id=to_node_id, slot_id=to_slot_id)
        )


class SceneData(BaseModel):
    uid: str = Field(default_factory=IDGenerator.generate_generic_id)

    dependencies: dict[str, str] # package_id -> version

    # FIXME on client: dependencies
    # remove node_types_id
    # remove node_types_version

    nodes: Dict[str, NodeSceneData] = Field(default_factory=dict)
    connections: Dict[str, ConnectionSceneData] = Field(default_factory=dict)

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)
