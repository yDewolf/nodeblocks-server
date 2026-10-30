from pydantic.dataclasses import dataclass
from nodeserver.engine.workers.protocols.ipc_protocol import IPCEvent

@dataclass(frozen=True)
class WorkerEvent(IPCEvent):
    pass

@dataclass(frozen=True)
class EvtWorkerReady(WorkerEvent):
    pass

@dataclass(frozen=True)
class EvtWorkerStopped(WorkerEvent):
    pass

@dataclass(frozen=True)
class EvtFatalError(WorkerEvent):
    error: str
