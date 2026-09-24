import uuid
from typing import Any, Optional
from enum import Enum

from nodeserver.engine.protocols.node_scene import NodeScene

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success" # Novo status para o TODO

class NodeExecutionStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class GraphRunContext:
    job_id: str
    scene: NodeScene
    status: JobStatus
    output_cache: dict[str, Any]
    
    errors: dict[str, str] # TODO: alterar isso aqui para um ErrorWrapper
    node_status: dict[str, NodeExecutionStatus]

    def __init__(self, scene: 'NodeScene'):
        self.job_id = str(uuid.uuid4())
        self.scene = scene
        self.status = JobStatus.PENDING
        
        self.output_cache = {}
        self.errors = {}
        self.node_status = {node_uid: NodeExecutionStatus.PENDING for node_uid in scene.graph.all_nodes.keys()}

    def get_cache_key(self, node_uid: str, slot_id: str) -> str:
        return f"{node_uid}:{slot_id}"
