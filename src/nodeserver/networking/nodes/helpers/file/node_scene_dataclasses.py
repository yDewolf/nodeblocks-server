import re
import uuid
from dataclasses import dataclass, field
from typing import Any

@dataclass
class NodeSceneData:
    id: str
    type: str
    data: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict, key: str) -> 'NodeSceneData':
        node_id = key
        if "_" in key:
            split = key.split("_")
            node_id = split[1] if len(split) >= 2 else key
        
        return cls(
            id=node_id,
            type=data.get("type", ""),
            data=data.get("data", {})
        )

@dataclass
class NodePathData:
    node_id: str
    slot_name: str | None = None

    @classmethod
    def from_str(cls, path: str) -> 'NodePathData':
        pattern = r"nodes:node_([^:\s]+):slots:([^:\s]+)"
        match = re.search(pattern, path, re.IGNORECASE)
        
        if match:
            return cls(
                node_id=match.group(1),
                slot_name=match.group(2)
            )

        return cls(node_id="")

@dataclass
class ConnectionSceneData:
    uid: str
    from_node: NodePathData
    to_node: NodePathData

    @classmethod
    def from_dict(cls, data: dict, key: str) -> 'ConnectionSceneData':
        conn_id = key
        return cls(
            uid=conn_id,
            from_node=NodePathData.from_str(data.get("from", "")),
            to_node=NodePathData.from_str(data.get("to", ""))
        )

@dataclass
class SceneData:
    uid: str
    node_types_id: str
    node_types_version: int
    nodes: dict[str, NodeSceneData]
    connections: dict[str, ConnectionSceneData]

    @classmethod
    def from_dict(cls, data: dict) -> 'SceneData':
        scene_id = data.get("scene_id", str(uuid.uuid4()))
        
        return cls(
            uid=scene_id,
            node_types_id=data.get("node_types_id", "unknown"),
            node_types_version=data.get("node_types_version", 0),
            nodes={
                key: NodeSceneData.from_dict(value, key) 
                for key, value in data.get("nodes", {}).items()
            },
            connections={
                key: ConnectionSceneData.from_dict(value, key) 
                for key, value in data.get("connections", {}).items()
            }
        )