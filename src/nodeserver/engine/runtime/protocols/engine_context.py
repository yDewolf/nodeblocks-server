from enum import StrEnum
from nodeserver.engine.protocols.node.node_scene import NodeScene

from abc import ABC, abstractmethod
from typing import Any, Optional

class NodeExecutionStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class EngineRuntimeContext(ABC):
    output_cache: dict[str, Any]
    errors: dict[str, str]
    node_status: dict[str, NodeExecutionStatus]

    def __init__(
        self,
        scene: NodeScene
    ) -> None:
        self.output_cache = {}
        self.errors = {}
        self.node_status = {node_uid: NodeExecutionStatus.PENDING for node_uid in scene.graph.all_nodes}

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

class EnclosedEngineContext(EngineRuntimeContext):
    _scene: NodeScene
    _persistent_cache: dict[str, dict[str, Any]]
    _node_hashes: dict[str, str]

    def __init__(
        self, 
        scene: NodeScene,
        persistent_cache: Optional[dict[str, dict]] = None,
    ) -> None:
        super().__init__(scene)
        self._scene = scene
        self._persistent_cache = persistent_cache if persistent_cache is not None else {}
        self._node_hashes = {}
    
    @property
    def scene(self): return self._scene
    @property
    def node_hashes(self): return self._node_hashes
    @property
    def persistent_cache(self): return self._persistent_cache
