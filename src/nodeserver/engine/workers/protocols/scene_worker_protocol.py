from dataclasses import dataclass
from typing import Optional
from nodeserver.engine.protocols.ipc_protocol import IPCCommandStatus, CmdStatus
from nodeserver.engine.runtime.engine_events import IPCEngineEvent

class IPCSceneWorkerEvent:
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
class SceneWorkerCommandResponse(IPCSceneWorkerEvent):
    status: CmdStatus

# Scene Actions:

@dataclass(frozen=True)
class SceneActionResult(SceneWorkerCommandResponse): pass

# Add Commands
@dataclass(frozen=True)
class AddNodeCommandResponse(SceneActionResult):
    node_uid: str

@dataclass(frozen=True)
class AddConnCommandResponse(SceneActionResult):
    conn_uid: str

