from dataclasses import dataclass
from typing import Optional

from nodeserver.engine.protocols.ipc_protocol import IPCEvent
from nodeserver.engine.runtime.protocols.engine_context import NodeExecutionStatus
from nodeserver.engine.runtime.job_runtime_context import JobStatus

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
