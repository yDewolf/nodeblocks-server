import re
import uuid
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Vector2:
    x: float
    y: float    

    @classmethod
    def from_dict(cls, data: dict) -> 'Vector2':
        return cls(
            x=data.get("x", 0),
            y=data.get("y", 0)
        )

    def serialize(self) -> list[float]:
        return [self.x, self.y]

@dataclass
class NodeSceneData:
    uid: str
    type: str
    position: Vector2
    data: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict, node_id: str) -> 'NodeSceneData':
        return cls(
            uid=node_id,
            type=data.get("type", ""),
            data=data.get("data", {}),
            position=Vector2.from_dict(data.get("position", {}))
        )

    def serialize(self) -> dict:
        return {
            "uid": self.uid,
            "type": self.type,
            "data": self.data,
            "position": self.position.serialize(),
        }

@dataclass
class NodePathData:
    node_id: str
    slot_name: str

    @classmethod
    def from_str(cls, path: str) -> 'NodePathData':
        pattern = r"nodes:([a-z0-9-]+):slots:([^:\s]+)"
        match = re.search(pattern, path, re.IGNORECASE)
        
        if match:
            return cls(
                node_id=match.group(1),
                slot_name=match.group(2)
            )

        return cls(node_id="", slot_name="")

    @staticmethod
    def make_path(node_id: str, slot_id: str) -> str:
        return f"nodes:{node_id}:slots:{slot_id}"

    def serialize(self) -> str:
        return self.make_path(self.node_id, self.slot_name)

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

    def serialize(self):
        return {
            "uid": self.uid,
            "from": self.from_node.serialize(),
            "to": self.to_node.serialize()
        }

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
    
    def serialize(self):
        return {
            "uid": self.uid,
            "node_types_id": self.node_types_id,
            "node_types_version": self.node_types_version,
            "nodes": {key: node.serialize() for key, node in self.nodes.items()},
            "connections": {key: conn.serialize() for key, conn in self.connections.items()}
        }