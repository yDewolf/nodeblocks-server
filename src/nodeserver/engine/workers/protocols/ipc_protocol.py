from pydantic import Field
from pydantic.dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Self

from nodeserver.protocols.helpers.uuid_utils import IDGenerator


class IPCCommandStatus(StrEnum):
    SUCCESSFUL = "successful"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"

@dataclass(frozen=True)
class CmdStatus:
    status: IPCCommandStatus
    message: Optional[str] = None

    @classmethod
    def failed(cls, message: Optional[str] = None) -> Self:
        return cls(status=IPCCommandStatus.FAILED, message=message)

    @classmethod
    def successful(cls, message: Optional[str] = None) -> Self:
        return cls(status=IPCCommandStatus.SUCCESSFUL, message=message)

    @classmethod
    def partial_success(cls, message: Optional[str] = None) -> Self:
        return cls(status=IPCCommandStatus.PARTIAL_SUCCESS, message=message)
    

@dataclass(frozen=True)
class IPCEvent:
    # Engine -> ...
    pass

@dataclass(frozen=True, kw_only=True)
class IPCCommand:
    # Server -> Worker
    request_id: str = Field(default_factory=lambda : IDGenerator.generate_generic_id(length=6))

@dataclass(frozen=True)
class IPCCommandResponse(IPCEvent):
    request_id: Optional[str]
    status: CmdStatus

    @classmethod
    def failed(cls, message: Optional[str] = None, request_id: Optional[str] = None, **kwargs):
        return cls(request_id=request_id, status=CmdStatus.failed(message), **kwargs)

    @classmethod
    def successful(cls, message: Optional[str] = None, request_id: Optional[str] = None, **kwargs):
        return cls(request_id=request_id, status=CmdStatus.successful(message), **kwargs)

    @classmethod
    def partial_success(cls, message: Optional[str] = None, request_id: Optional[str] = None, **kwargs):
        return cls(request_id=request_id, status=CmdStatus.partial_success(message), **kwargs)
    

    @property
    def is_success(self):
        return self.status.status == IPCCommandStatus.SUCCESSFUL

@dataclass(frozen=True)
class MultipleStatusCommandResponse(IPCCommandResponse):
    statuses: dict[str, CmdStatus]
        
    @classmethod
    def new(cls, statuses: dict[str, CmdStatus], message: str | None = None, request_id: str | None = None):
        status_values = statuses.values()
        has_success = IPCCommandStatus.SUCCESSFUL in status_values
        has_failed = IPCCommandStatus.FAILED in status_values

        if has_success and not has_failed:
            return super().successful(message, request_id, statuses=statuses)
        
        if has_failed and not has_success:
            return super().failed(message, request_id, statuses=statuses)

        return super().partial_success(message, request_id, statuses=statuses)
