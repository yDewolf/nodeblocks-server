from pydantic.dataclasses import dataclass
from enum import StrEnum
from typing import Any, Optional

from nodeserver.engine.runtime.protocols.engine_tracker import EngineTracker
from nodeserver.engine.workers.protocols.ipc_protocol import IPCEvent

@dataclass(frozen=True)
class IPCEngineEvent(IPCEvent):
    job_id: str
    tracker: Optional[EngineTracker]


class NodeExecutionStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass(frozen=True)
class EvtNodeStatusChanged(IPCEngineEvent):
    node_uid: str
    status: NodeExecutionStatus

    node_result: Optional[dict[str, Any]]

@dataclass(frozen=True)
class EvtFailedProcess(IPCEngineEvent):
    error: str


@dataclass
class EngineError:
    tracker: EngineTracker
    message: str

@dataclass(frozen=True)
class EvtRuntimeError(IPCEngineEvent):
    message: str


# TODO: these should be in another file
class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"

@dataclass(frozen=True)
class EvtJobStatusChanged(IPCEngineEvent):
    status: JobStatus

