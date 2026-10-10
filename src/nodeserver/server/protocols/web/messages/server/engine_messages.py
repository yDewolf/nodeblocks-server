
from enum import StrEnum
from typing import Annotated, Literal, Optional, Union
from pydantic import BaseModel, Field

from nodeserver.engine.runtime.protocols.engine_context import NodeExecutionStatus
from nodeserver.engine.runtime.protocols.engine_events import JobStatus


class EngineEventTypes(StrEnum):
    NODE_STATUS = "node_status_changed"
    JOB_STATUS = "job_status_changed"
    FAILED_PROCESS = "failed_process"

class EngineEventPayload(BaseModel):
    type: EngineEventTypes
    job_id: str


class NodeStatusPayload(EngineEventPayload):
    type: Literal[EngineEventTypes.NODE_STATUS] = EngineEventTypes.NODE_STATUS
    node_uid: str
    status: NodeExecutionStatus
    
    node_result: Optional[dict]

class JobStatusPayload(EngineEventPayload):
    type: Literal[EngineEventTypes.JOB_STATUS] = EngineEventTypes.JOB_STATUS
    status: JobStatus

class FailedProcessPayload(EngineEventPayload):
    type: Literal[EngineEventTypes.FAILED_PROCESS] = EngineEventTypes.FAILED_PROCESS
    error: str


EngineEventPayloadAdapter = Annotated[
    Union[NodeStatusPayload, JobStatusPayload, FailedProcessPayload],
    Field(discriminator="type")
]