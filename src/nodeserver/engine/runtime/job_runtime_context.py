from typing import Any, Callable, Optional
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.runtime.protocols.engine_context import EngineRuntimeContext, NodeExecutionStatus
from nodeserver.engine.runtime.protocols.engine_events import EvtJobStatusChanged, EvtNodeStatusChanged, IPCEngineEvent, JobStatus
from nodeserver.protocols.helpers.uuid_utils import IDGenerator

class SceneSuperContext:
    scene: NodeScene
    persistent_cache: dict[str, dict[str, Any]]
    node_hashes: dict[str, str]
    
    _emit_event_callback: Optional[Callable[[IPCEngineEvent], None]]

    def __init__(
        self, 
        scene: NodeScene,
        emit_event_callback: Optional[Callable[[IPCEngineEvent], None]] = None,
        persistent_cache: Optional[dict[str, dict]] = None,
    ):
        self.scene = scene
        self._emit_event_callback = emit_event_callback
        self.persistent_cache = persistent_cache if persistent_cache is not None else {}
        self.node_hashes = {}

    def invalidate_node_cache(self, node_uid: str, recursive: bool = True):
        self.persistent_cache.pop(node_uid, None)
        self.node_hashes.pop(node_uid, None)

        if recursive:
            downstream = self.scene.graph.get_downstream_node_ids(node_uid)
            for d_uid in downstream:
                self.invalidate_node_cache(d_uid, recursive=False)

    def emit_event(self, event: IPCEngineEvent):
        if self._emit_event_callback:
            self._emit_event_callback(event)


class JobExecutionContext(EngineRuntimeContext):
    global_context: SceneSuperContext
    job_id: str
    status: JobStatus
    target_nodes: Optional[list[str]]

    def __init__(
        self, 
        runtime: SceneSuperContext, 
        job_id: Optional[str] = None,
        target_nodes: Optional[list[str]] = None
    ):
        self.global_context = runtime
        self.job_id = job_id or IDGenerator.generate_generic_id(6)
        self.status = JobStatus.PENDING
        self.target_nodes = target_nodes

        super().__init__(runtime.scene)
        nodes_to_track = target_nodes if target_nodes else list(runtime.scene.graph.all_nodes.keys())
        self.node_status = {node_uid: NodeExecutionStatus.PENDING for node_uid in nodes_to_track}

    def update_node_status(self, node_uid: str, status: NodeExecutionStatus, result: Any = None):
        super().update_node_status(node_uid, status)
        self.global_context.emit_event(EvtNodeStatusChanged(node_uid, status, node_result=result))

    def set_job_status(self, status: JobStatus):
        self.status = status
        self.global_context.emit_event(EvtJobStatusChanged(status))

    @property
    def scene(self) -> NodeScene:
        return self.global_context.scene

    @property
    def node_hashes(self) -> dict[str, str]:
        return self.global_context.node_hashes

    @property
    def persistent_cache(self) -> dict[str, dict[str, Any]]:
        return self.global_context.persistent_cache

