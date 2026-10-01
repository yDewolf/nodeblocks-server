from dataclasses import dataclass
from typing import Optional
from nodeserver.engine.protocols.ipc_protocol import IPCCommandResponse, IPCCommandStatus, CmdStatus, IPCEvent
from nodeserver.engine.runtime.engine_events import IPCEngineEvent

class IPCSceneWorkerEvent(IPCEvent):
    pass

@dataclass(frozen=True)
class EvtWorkerReady(IPCSceneWorkerEvent):
    pass

@dataclass(frozen=True)
class EvtFatalError(IPCSceneWorkerEvent):
    error: str

@dataclass(frozen=True)
class WorkerEngineEventWrapper(IPCSceneWorkerEvent):
    engine_event: IPCEngineEvent


# Command Responses

@dataclass(frozen=True)
class SceneWorkerCommandResponse(IPCCommandResponse, IPCSceneWorkerEvent):
    pass

# Scene Actions:

@dataclass(frozen=True)
class SceneActionResult(SceneWorkerCommandResponse): pass

# Add Commands
@dataclass(frozen=True)
class AddNodeCommandResponse(SceneActionResult):
    node_uid: Optional[str]

    @classmethod
    def successful(cls, node_uid: str, message: str | None = None, request_id: str | None = None):
        return super().successful(message, request_id, node_uid=node_uid)

    @classmethod
    def failed(cls, message: str | None = None, request_id: str | None = None):
        return super().failed(message, request_id, node_uid=None)

@dataclass(frozen=True)
class AddConnCommandResponse(SceneActionResult):
    conn_uid: str

