from pydantic.dataclasses import dataclass


from typing import Optional


@dataclass
class EngineTracker:
    node_id: Optional[str] = None
    slot_id: Optional[str] = None
    param_id: Optional[str] = None
    conn_id: Optional[str] = None
    other: Optional[dict[str, str]] = None

    @classmethod
    def node(cls, node_id: str, other: Optional[dict[str, str]] = None):
        return cls(node_id=node_id, other=other)

    @classmethod
    def slot(cls, node_id: str, slot_id: str, other: Optional[dict[str, str]] = None):
        return cls(node_id=node_id, slot_id=slot_id, other=other)

    @classmethod
    def param(cls, node_id: str, param_id: str, other: Optional[dict[str, str]] = None):
        return cls(node_id=node_id, param_id=param_id, other=other)

    @classmethod
    def conn(cls, conn_id: str, other: Optional[dict[str, str]] = None):
        return cls(conn_id=conn_id, other=other)
