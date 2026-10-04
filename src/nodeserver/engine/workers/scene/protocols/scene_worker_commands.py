from dataclasses import dataclass, field
from typing import Any, Optional

from nodeserver.engine.workers.protocols.ipc_protocol import IPCCommand
from nodeserver.engine.workers.scene.protocols.scene_worker_states import SceneWorkerExecutionMode, SceneWorkerExecutionState
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData, SceneData
from nodeserver.protocols.manifest.structs.scene_structs import Vector2


class IPCSceneWorkerCommand(IPCCommand):
    pass

@dataclass(frozen=True)
class StopWorkerCommand(IPCSceneWorkerCommand): pass


# Mode Updates
class RuntimeCommand(IPCSceneWorkerCommand):
    pass

@dataclass(frozen=True)
class UpdateExecutionStateCmd(RuntimeCommand):
    state: SceneWorkerExecutionState
    # iteration is a full graph (or full subgraph) execution
    target_iterations: Optional[int] = None

@dataclass(frozen=True)
class UpdateExecutionModeCmd(RuntimeCommand):
    mode: SceneWorkerExecutionMode

@dataclass(frozen=True)
class UpdateTargetNodesCmd(RuntimeCommand):
    target_nodes: Optional[list[str]]


@dataclass(frozen=True)
class PauseGraphCommand(RuntimeCommand): pass

@dataclass(frozen=True)
class GraphStepCommand(RuntimeCommand): 
    pass


# Scene Commands
class SceneUpdateCommand(IPCSceneWorkerCommand):
    pass

@dataclass(frozen=True)
class ResetSceneCommand(SceneUpdateCommand):
    pass

@dataclass(frozen=True)
class LoadSceneCommand(SceneUpdateCommand):
    scene_uid: str
    create_if_nonexistent: bool = False

@dataclass(frozen=True)
class LoadSceneDataCommand(SceneUpdateCommand):
    scene_data: SceneData


@dataclass(frozen=True)
class AddNodeCommand(SceneUpdateCommand):
    nodetype_fqn: str
    node_data: Optional[NodeSceneData]


@dataclass(frozen=True)
class AddConnectionCommand(SceneUpdateCommand):
    from_node_id: str
    from_slot_id: str
    to_node_id: str
    to_slot_id: str

# Node Commands

class SceneWorkerNodeCommand(SceneUpdateCommand):
    node_uid: str

@dataclass(frozen=True)
class UpdateNodeCommand(SceneWorkerNodeCommand):
    position: Optional[Vector2] = None
    data: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class RemoveNodeCommand(SceneWorkerNodeCommand):
    pass


# Connection Commands:
class SceneWorkerConnCommand(SceneUpdateCommand):
    conn_uid: str

@dataclass(frozen=True)
class RemoveConnectionCommand(SceneWorkerConnCommand):
    pass
