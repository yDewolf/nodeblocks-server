from enum import StrEnum

from nodeserver.engine.runtime.protocols.engine_events import IPCEngineEvent
from pydantic.dataclasses import dataclass

class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"


@dataclass(frozen=True)
class EvtJobStatusChanged(IPCEngineEvent):
    status: JobStatus
