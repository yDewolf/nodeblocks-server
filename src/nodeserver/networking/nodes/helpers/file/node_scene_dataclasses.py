from dataclasses import dataclass
import re
from typing import Any

@dataclass
class NodeSceneData:
    id: int
    type: str
    # position: Vector2
    # size: Vector2
    data: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict, key: str) -> 'NodeSceneData':
        node_id = -1
        split = key.split("_")
        if len(split) >= 2:
            node_id = int(split[1])

        return cls(
            id=node_id,
            type=data.get("type", ""),
            # position=Vector2.from_list(data.get("position", [0, 0])),
            # size=Vector2.from_list(data.get("size", [0, 0])),
            data=data.get("data", {})
        )

@dataclass
class NodePathData:
    node_id: int
    slot_name: str | None = None

    @classmethod
    def from_str(cls, path: str) -> 'NodePathData':
        pattern = r"nodes:node_(\d+):slots:([^:\s]+)"
        match = re.search(pattern, path, re.IGNORECASE)
        
        if match:
            return cls(
                node_id=int(match.group(1)),
                slot_name=match.group(2) if len(match.groups()) > 1 else None
            )

        return cls(node_id=-1)


@dataclass
class ConnectionSceneData:
    from_node: NodePathData
    to_node: NodePathData

    @classmethod
    def from_dict(cls, data: dict) -> 'ConnectionSceneData':
        return cls(
            from_node=NodePathData.from_str(data.get("from", "")),
            to_node=NodePathData.from_str(data.get("to", ""))
        )

@dataclass
class SceneData:
    node_types_id: str
    node_types_version: int
    nodes: dict[str, NodeSceneData]
    connections: dict[str, ConnectionSceneData]

    @classmethod
    def from_dict(cls, data: dict) -> 'SceneData':
        return cls(
            node_types_id=data.get("node_types_id", "unknown"),
            node_types_version=data.get("node_types_version", 0),
            nodes={
                key: NodeSceneData.from_dict(value, key) 
                for key, value in data.get("nodes", {}).items()
            },
            connections={
                key: ConnectionSceneData.from_dict(value) 
                for key, value in data.get("connections", {}).items()
            }
        )

