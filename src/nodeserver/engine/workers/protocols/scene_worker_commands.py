from dataclasses import dataclass, field
from typing import Any, Optional

from nodeserver.engine.protocols.ipc_protocol import IPCCommand
from nodeserver.engine.workers.protocols.scene_worker_states import SceneWorkerExecutionMode, SceneWorkerExecutionState
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData, SceneData
from nodeserver.protocols.manifest.structs.scene_structs import Vector2


class IPCSceneWorkerCommand(IPCCommand):
    pass

@dataclass(frozen=True)
class StopWorkerCommand(IPCSceneWorkerCommand): pass


# Mode Updates

@dataclass(frozen=True)
class UpdateExecutionStateCmd(IPCSceneWorkerCommand):
    state: SceneWorkerExecutionState
    # iteration is a full graph (or full subgraph) execution
    target_iterations: Optional[int] = None

@dataclass(frozen=True)
class UpdateExecutionModeCmd(IPCSceneWorkerCommand):
    mode: SceneWorkerExecutionMode

@dataclass(frozen=True)
class UpdateTargetNodesCmd(IPCSceneWorkerCommand):
    target_nodes: Optional[list[str]]


@dataclass(frozen=True)
class PauseGraphCommand(IPCSceneWorkerCommand): pass

@dataclass(frozen=True)
class GraphStepCommand(IPCSceneWorkerCommand): 
    pass


# Scene Commands
@dataclass(frozen=True)
class LoadSceneCommand(IPCSceneWorkerCommand):
    scene_data: SceneData


@dataclass(frozen=True)
class AddNodeCommand(IPCSceneWorkerCommand):
    nodetype_fqn: str
    node_data: Optional[NodeSceneData]


@dataclass(frozen=True)
class AddConnectionCommand(IPCSceneWorkerCommand):
    from_node_id: str
    from_slot_id: str
    to_node_id: str
    to_slot_id: str

# Node Commands

@dataclass(frozen=True)
class SceneWorkerNodeCommand(IPCSceneWorkerCommand):
    node_uid: str

@dataclass(frozen=True)
class UpdateNodeCommand(SceneWorkerNodeCommand):
    position: Optional[Vector2] = None
    data: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class RemoveNodeCommand(SceneWorkerNodeCommand):
    pass


# Connection Commands:

@dataclass(frozen=True)
class RemoveConnectionCommand(IPCSceneWorkerCommand):
    conn_uid: str
