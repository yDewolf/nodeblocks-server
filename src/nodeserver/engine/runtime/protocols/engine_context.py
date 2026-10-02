from enum import StrEnum
from nodeserver.engine.protocols.node.node_scene import NodeScene

from abc import ABC, abstractmethod
from typing import Any

class NodeExecutionStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class EngineRuntimeContext(ABC):
    output_cache: dict[str, Any]
    errors: dict[str, str]
    node_status: dict[str, NodeExecutionStatus]

    @property
    @abstractmethod
    def scene(self) -> NodeScene: pass

    @property
    @abstractmethod
    def node_hashes(self) -> dict[str, str]: pass

    @property
    @abstractmethod
    def persistent_cache(self) -> dict[str, dict[str, Any]]: pass

    def update_node_status(self, node_uid: str, status: NodeExecutionStatus, result: Any = None):
        if node_uid in self.node_status:
            self.node_status[node_uid] = status

    def get_cache_key(self, node_uid: str, slot_id: str) -> str:
        return f"{node_uid}:{slot_id}"

