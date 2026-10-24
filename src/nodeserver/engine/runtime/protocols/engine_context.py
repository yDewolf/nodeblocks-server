from nodeserver.engine.protocols.node.logic_nodes import NodeInputs
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.runtime.protocols.engine_events import EngineError, NodeExecutionStatus

from abc import ABC, abstractmethod
from typing import Any, Optional

class ContextInjector(ABC):
    id: str
    def __init__(self) -> None:
        self.id = self.__class__.__name__

    @abstractmethod
    def inject_context(self, raw_inputs: dict[str, Any], InputModel: type[NodeInputs]):
        pass


class EngineRuntimeContext(ABC):
    output_cache: dict[str, Any]
    errors: list[EngineError]
    node_status: dict[str, NodeExecutionStatus]

    def __init__(
        self,
        scene: NodeScene
    ) -> None:
        self.output_cache = {}
        self.errors = []
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

    def update_node_status(self, node_uid: str, status: NodeExecutionStatus, result: Optional[dict[str, Any]] = None):
        if node_uid in self.node_status:
            self.node_status[node_uid] = status

    def get_cache_key(self, node_uid: str, slot_id: str) -> str:
        return f"{node_uid}:{slot_id}"

    def add_error(self, error: EngineError):
        self.errors.append(error)

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
