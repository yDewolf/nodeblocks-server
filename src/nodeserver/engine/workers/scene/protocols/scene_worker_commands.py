from dataclasses import dataclass, field
from typing import Any, Optional

from nodeserver.engine.workers.protocols.ipc_protocol import IPCCommand
from nodeserver.engine.workers.scene.protocols.scene_worker_states import SceneWorkerExecutionMode, SceneWorkerExecutionState
from nodeserver.protocols.manifest.node.node_graph import ConnectionSceneData, NodeSceneData, SceneData
from nodeserver.protocols.manifest.structs.scene_structs import Vector2


class IPCSceneWorkerCommand(IPCCommand):
    pass

@dataclass(frozen=True)
class StopWorkerCommand(IPCSceneWorkerCommand): pass
@dataclass(frozen=True)
class CheckExecutionState(IPCSceneWorkerCommand): pass

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


class SceneGraphCommand(SceneUpdateCommand):
    pass


@dataclass(frozen=True)
class AddNodeData:
    nodetype_fqn: str
    node_data: Optional[NodeSceneData]

@dataclass(frozen=True)
class AddNodesCommand(SceneGraphCommand):
    nodes: list[AddNodeData]
    
    @classmethod
    def single(cls, nodetype_fqn: str, node_data: Optional[NodeSceneData]):
        return cls(nodes=[AddNodeData(
            nodetype_fqn=nodetype_fqn,
            node_data=node_data
        )])

@dataclass(frozen=True)
class AddConnectionCommand(SceneGraphCommand):
    from_node_id: str
    from_slot_id: str
    to_node_id: str
    to_slot_id: str

# Node Commands

@dataclass(frozen=True)
class UpdateNodeData:
    position: Optional[Vector2] = None
    data: dict[str, Any] = field(default_factory=dict)
@dataclass(frozen=True)
class UpdateNodesCommand(SceneGraphCommand):
    nodes: dict[str, UpdateNodeData]

@dataclass(frozen=True)
class RemoveNodesCommand(SceneGraphCommand):
    uids: list[str]

# Connection Commands:
class SceneWorkerConnCommand(SceneGraphCommand):
    conn_uid: str

@dataclass(frozen=True)
class RemoveConnectionCommand(SceneWorkerConnCommand):
    pass
