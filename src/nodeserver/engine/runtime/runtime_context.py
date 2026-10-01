import uuid
from typing import Any, Callable, Optional
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.runtime.engine_events import EvtJobStatusChanged, EvtNodeStatusChanged, IPCEngineEvent, JobStatus, NodeExecutionStatus


class GraphRunContext:
    scene: NodeScene
    
    job_id: str
    status: JobStatus
    
    output_cache: dict[str, Any]
    errors: dict[str, str] # TODO: alterar isso aqui para um ErrorWrapper
    node_status: dict[str, NodeExecutionStatus]

    node_hashes: dict[str, str]
    persistent_cache: dict[str, dict[str, Any]] # node_uid -> {slot_id -> output_value}

    _emit_event_callback: Optional[Callable[[IPCEngineEvent], None]]

    def __init__(
        self, 
        scene: NodeScene,
        emit_event_callback: Optional[Callable[[IPCEngineEvent], None]] = None,
        persistent_cache: Optional[dict[str, dict]] = None,
        job_id: Optional[str] = None,
    ):
        self.job_id = job_id or str(uuid.uuid4())
        self.scene = scene
        self.status = JobStatus.PENDING
        
        self.errors = {}
        self.node_status = {node_uid: NodeExecutionStatus.PENDING for node_uid in scene.graph.all_nodes.keys()}
        
        self.output_cache = {}
        self.node_hashes = {}
        self.persistent_cache = persistent_cache if persistent_cache is not None else {}

        self._emit_event_callback = emit_event_callback

    # Context Updates:

    def update_node_status(self, node_uid: str, status: NodeExecutionStatus, result: Any = None):
        self.node_status[node_uid] = status
        self._emit_event(EvtNodeStatusChanged(
            node_uid, status, node_result=result
        ))

    def set_job_status(self, status: JobStatus):
        self.status = status
        self._emit_event(EvtJobStatusChanged(status))

    # Pre Engine Processing

    def prepare_for_run(self, node_uids: Optional[list[str]] = None):
        uids_to_reset = node_uids if node_uids is not None else list(self.scene.graph.all_nodes.keys())
        for uid in uids_to_reset:
            self._reset_node_status(uid)

    def invalidate_node_cache(self, node_uid: str, recursive: bool = True):
        self.persistent_cache.pop(node_uid, None)
        self.node_hashes.pop(node_uid, None)

        if recursive:
            downstream = self.scene.graph.get_downstream_node_ids(node_uid)
            for d_uid in downstream:
                self.invalidate_node_cache(d_uid, recursive=False)

    # Utility

    def _reset_node_status(self, node_uid: str):
        self.node_status[node_uid] = NodeExecutionStatus.PENDING
        self.errors.pop(node_uid, None)

    def _emit_event(self, event: IPCEngineEvent):
        if self._emit_event_callback:
            self._emit_event_callback(event)

    def get_cache_key(self, node_uid: str, slot_id: str) -> str:
        return f"{node_uid}:{slot_id}"
