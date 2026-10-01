from dataclasses import dataclass

from nodeserver.engine.protocols.ipc_protocol import IPCEvent
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
