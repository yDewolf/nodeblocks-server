from pydantic.dataclasses import dataclass
from enum import StrEnum
from typing import Optional

from nodeserver.engine.workers.protocols.ipc_protocol import IPCEvent
from nodeserver.engine.runtime.protocols.engine_context import NodeExecutionStatus

@dataclass(frozen=True)
class IPCEngineEvent(IPCEvent):
    job_id: str

@dataclass(frozen=True)
class EvtNodeStatusChanged(IPCEngineEvent):
    node_uid: str
    status: NodeExecutionStatus

    node_result: Optional[dict]

@dataclass(frozen=True)
class EvtFailedProcess(IPCEngineEvent):
    error: str


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"

@dataclass(frozen=True)
class EvtJobStatusChanged(IPCEngineEvent):
    status: JobStatus



