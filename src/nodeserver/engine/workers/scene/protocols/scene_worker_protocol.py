from pydantic.dataclasses import dataclass
from typing import Optional, Protocol
from nodeserver.engine.workers.protocols.ipc_protocol import IPCCommandResponse, IPCEvent
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.runtime.protocols.engine_events import IPCEngineEvent
from nodeserver.engine.workers.scene.protocols.scene_worker_states import SceneWorkerExecutionMode, SceneWorkerExecutionState
from nodeserver.protocols.manifest.node.node_graph import SceneData

class ISceneWorker(Protocol):
    scene_id: str

    def on_runtime_updated(self, state: SceneWorkerExecutionState, mode: SceneWorkerExecutionMode):
        pass

    def engine_event_receiver(self, event: IPCEngineEvent):
        pass

    def _create_new_scene(self, scene_data: SceneData) -> NodeScene:
        raise NotImplementedError()


# IPC
@dataclass(frozen=True)
class IPCSceneWorkerEvent(IPCEvent):
    pass

@dataclass(frozen=True)
class WorkerEngineEventWrapper(IPCSceneWorkerEvent):
    engine_event: IPCEngineEvent


# Command Responses
@dataclass(frozen=True)
class SceneWorkerCommandResponse(IPCCommandResponse, IPCSceneWorkerEvent):
    pass


# Check Responses
@dataclass(frozen=True)
class UpdateExecutionConfigResponse(SceneWorkerCommandResponse):
    state: SceneWorkerExecutionState
    mode: SceneWorkerExecutionMode
    target_nodes: Optional[list[str]]
    target_iterations: Optional[int]

    @classmethod
    def successful(
        cls, 
        state: SceneWorkerExecutionState, mode: SceneWorkerExecutionMode, 
        target_nodes: Optional[list[str]], target_iterations: Optional[int],
        request_id: str | None = None
    ):
        return super().successful("", request_id, state=state, target_nodes=target_nodes, target_iterations=target_iterations, mode=mode)


@dataclass(frozen=True)
class GetSceneDataResponse(SceneWorkerCommandResponse):
    scene_data: Optional[SceneData]

    @classmethod
    def successful(cls, scene_data: SceneData, message: str | None = None, request_id: str | None = None):
        return super().successful(message, request_id, scene_data=scene_data)

    @classmethod
    def failed(cls, message: str | None = None, request_id: str | None = None):
        return super().failed(message, request_id, scene_data=None)


@dataclass(frozen=True)
class SaveSceneResponse(SceneWorkerCommandResponse):
    pass

# Scene Actions:

@dataclass(frozen=True)
class SceneActionResult(SceneWorkerCommandResponse): pass

# Add Commands
@dataclass(frozen=True)
class AddNodeCommandResponse(SceneActionResult):
    nodes: Optional[list[str]]

    @classmethod
    def successful(cls, added_nodes: list[str], message: str | None = None, request_id: str | None = None):
        return super().successful(message, request_id, nodes=added_nodes)

    @classmethod
    def failed(cls, message: str | None = None, request_id: str | None = None):
        return super().failed(message, request_id, nodes=None)

@dataclass(frozen=True)
class AddConnCommandResponse(SceneActionResult):
    conns: Optional[list[str]]

    
    @classmethod
    def successful(cls, conns: list[str], message: str | None = None, request_id: str | None = None):
        return super().successful(message, request_id, conns=conns)

    @classmethod
    def failed(cls, message: str | None = None, request_id: str | None = None):
        return super().failed(message, request_id, conns=None)
