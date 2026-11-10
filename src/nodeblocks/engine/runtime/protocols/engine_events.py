from pydantic.dataclasses import dataclass
from enum import StrEnum
from typing import Any, Optional, Union

from nodeblocks.protocols.manifest.node.datatype_value_meta import SerializedDataTypeValue
from nodeblocks.engine.runtime.protocols.engine_tracker import EngineTracker
from nodeblocks.engine.workers.protocols.ipc_protocol import IPCEvent

@dataclass(frozen=True)
class IPCEngineEvent(IPCEvent):
    job_id: str
    tracker: Optional[EngineTracker]


class NodeExecutionStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class IPCEngineNodeEvent(IPCEngineEvent):
    node_uid: str

@dataclass(frozen=True)
class EvtNodeStatusChanged(IPCEngineNodeEvent):
    node_uid: str
    status: NodeExecutionStatus

    node_result: Optional[dict[str, Union[SerializedDataTypeValue, Any]]]

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

