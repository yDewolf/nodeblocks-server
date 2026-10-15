from pydantic.dataclasses import dataclass


from typing import Optional


@dataclass
class EngineTracker:
    node_id: Optional[str] = None
    slot_id: Optional[str] = None
    param_id: Optional[str] = None
    conn_id: Optional[str] = None

    @classmethod
    def node(cls, node_id: str):
        return cls(node_id=node_id)

    @classmethod
    def slot(cls, node_id: str, slot_id: str):
        return cls(node_id=node_id, slot_id=slot_id)

    @classmethod
    def param(cls, node_id: str, param_id: str):
        return cls(node_id=node_id, param_id=param_id)

    @classmethod
    def conn(cls, conn_id: str):
        return cls(conn_id=conn_id)
