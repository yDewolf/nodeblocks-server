
from enum import StrEnum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class WorkerEventTypes(StrEnum):
    READY = "ready"
    STOPPED = "stopped"
    FATAL_ERROR = "fatal_error"

class BaseWorkerEventPayload(BaseModel):
    type: WorkerEventTypes


class WorkerReadyPayload(BaseWorkerEventPayload):
    type: Literal[WorkerEventTypes.READY] = WorkerEventTypes.READY

class WorkerStoppedPayload(BaseWorkerEventPayload):
    type: Literal[WorkerEventTypes.STOPPED] = WorkerEventTypes.STOPPED

class WorkerFatalErrorPayload(BaseWorkerEventPayload):
    type: Literal[WorkerEventTypes.FATAL_ERROR] = WorkerEventTypes.FATAL_ERROR
    error: str


WorkerEventPayloadAdapter = Annotated[
    Union[WorkerReadyPayload, WorkerStoppedPayload, WorkerFatalErrorPayload],
    Field(discriminator="type")
]
