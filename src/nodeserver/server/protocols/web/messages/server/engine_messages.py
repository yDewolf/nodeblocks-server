
from enum import StrEnum
from typing import Annotated, Literal, Optional, Union
from nodeserver.protocols.manifest.node.datatype_value_meta import SerializedDataTypeValue
from pydantic import BaseModel, Field

from nodeserver.engine.runtime.protocols.engine_events import NodeExecutionStatus
from nodeserver.engine.runtime.protocols.engine_events import JobStatus
from nodeserver.engine.runtime.protocols.engine_tracker import EngineTracker


class EngineEventTypes(StrEnum):
    NODE_STATUS = "node_status_changed"
    JOB_STATUS = "job_status_changed"
    FAILED_PROCESS = "failed_process"
    RUNTIME_ERROR = "runtime_error"

class EngineEventPayload(BaseModel):
    type: EngineEventTypes
    tracker: Optional[EngineTracker] = None
    job_id: str


class NodeStatusPayload(EngineEventPayload):
    type: Literal[EngineEventTypes.NODE_STATUS] = EngineEventTypes.NODE_STATUS
    node_uid: str
    status: NodeExecutionStatus
    
    node_result: Optional[dict[str, SerializedDataTypeValue]]

class JobStatusPayload(EngineEventPayload):
    type: Literal[EngineEventTypes.JOB_STATUS] = EngineEventTypes.JOB_STATUS
    status: JobStatus

class FailedProcessPayload(EngineEventPayload):
    type: Literal[EngineEventTypes.FAILED_PROCESS] = EngineEventTypes.FAILED_PROCESS
    error: str


class RuntimeErrorPayload(EngineEventPayload):
    type: Literal[EngineEventTypes.RUNTIME_ERROR] = EngineEventTypes.RUNTIME_ERROR
    message: str

EngineEventPayloadAdapter = Annotated[
    Union[NodeStatusPayload, JobStatusPayload, FailedProcessPayload, RuntimeErrorPayload],
    Field(discriminator="type")
]