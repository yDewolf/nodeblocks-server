from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional, Self

from nodeserver.protocols.helpers.uuid_utils import IDGenerator


class IPCCommandStatus(StrEnum):
    SUCCESSFUL = "successful"
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


class IPCEvent:
    # Engine -> ...
    pass

@dataclass(frozen=True, kw_only=True)
class IPCCommand:
    # Server -> Worker
    request_id: str = IDGenerator.generate_generic_id(length=4)

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

    @property
    def is_success(self):
        return self.status.status == IPCCommandStatus.SUCCESSFUL
