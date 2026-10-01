from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Self


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


class IPCCommand:
    # Server -> Worker
    pass


class IPCEvent:
    # Engine -> ...
    pass

