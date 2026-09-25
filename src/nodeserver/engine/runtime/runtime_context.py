import uuid
from typing import Any, Optional
from enum import Enum

from nodeserver.engine.protocols.node.node_scene import NodeScene

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"

class NodeExecutionStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class GraphRunContext:
    job_id: str
    scene: NodeScene
    status: JobStatus
    
    output_cache: dict[str, Any] # this run only
    errors: dict[str, str] # TODO: alterar isso aqui para um ErrorWrapper
    node_status: dict[str, NodeExecutionStatus]

    node_hashes: dict[str, str]
    persistent_cache: dict[str, dict]

    def __init__(self, scene: NodeScene, persistent_cache: Optional[dict[str, dict]] = None):
        self.job_id = str(uuid.uuid4())
        self.scene = scene
        self.status = JobStatus.PENDING
        
        self.errors = {}
        self.node_status = {node_uid: NodeExecutionStatus.PENDING for node_uid in scene.graph.all_nodes.keys()}
        
        self.output_cache = {}
        self.node_hashes = {}
        self.persistent_cache = persistent_cache if persistent_cache is not None else {}

    def get_cache_key(self, node_uid: str, slot_id: str) -> str:
        return f"{node_uid}:{slot_id}"
