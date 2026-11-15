from dataclasses import dataclass
from enum import StrEnum
from typing import Optional


# FIXME: talvez usar JobStatus
class TaskState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ServerTask:
    id: str
    name: str
    state: TaskState
    message: Optional[str] = None
