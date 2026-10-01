from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Optional

from nodeserver.engine.protocols.ipc_protocol import IPCEvent

class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"

class NodeExecutionStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class IPCEngineEvent(IPCEvent):
    job_id: str

@dataclass(frozen=True)
class EvtNodeStatusChanged(IPCEngineEvent):
    node_uid: str
    status: NodeExecutionStatus

    node_result: Optional[dict]


@dataclass(frozen=True)
class EvtJobStatusChanged(IPCEngineEvent):
    status: JobStatus


@dataclass(frozen=True)
class EvtFailedProcess(IPCEngineEvent):
    error: str
