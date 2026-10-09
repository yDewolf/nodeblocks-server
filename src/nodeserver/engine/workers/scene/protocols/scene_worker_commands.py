from pydantic import Field
from pydantic.dataclasses import dataclass
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

@dataclass(frozen=True)
class GetSceneDataCommand(IPCSceneWorkerCommand):
    pass

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
class SaveSceneCommand(SceneUpdateCommand):
    pass



class SceneGraphCommand(SceneUpdateCommand):
    pass


@dataclass(frozen=True)
class AddNodeData:
    uid: Optional[str]
    nodetype_fqn: str
    node_data: Optional[NodeSceneData]

@dataclass(frozen=True)
class AddNodesCommand(SceneGraphCommand):
    nodes: list[AddNodeData]
    
    @classmethod
    def single(cls, nodetype_fqn: str, node_data: Optional[NodeSceneData], uid: Optional[str] = None):
        return cls(nodes=[AddNodeData(
            uid=uid,
            nodetype_fqn=nodetype_fqn,
            node_data=node_data
        )])

@dataclass(frozen=True)
class AddConnData:
    uid: Optional[str]
    from_node_id: str
    from_slot_id: str
    to_node_id: str
    to_slot_id: str

@dataclass(frozen=True)
class AddConnectionsCommand(SceneGraphCommand):
    connections: list[AddConnData]

    @classmethod
    def single(
        cls,
        uid: str,
        from_node_id: str,
        from_slot_id: str,
        to_node_id: str,
        to_slot_id: str
    ):
        return cls(connections=[AddConnData(
            uid=uid,
            from_node_id=from_node_id,
            from_slot_id=from_slot_id,
            to_node_id=to_node_id,
            to_slot_id=to_slot_id
        )])

# Node Commands

@dataclass(frozen=True)
class UpdateNodeData:
    position: Optional[Vector2] = None
    data: dict[str, Any] = Field(default_factory=dict)
@dataclass(frozen=True)
class UpdateNodesCommand(SceneGraphCommand):
    nodes: dict[str, UpdateNodeData]

@dataclass(frozen=True)
class RemoveNodesCommand(SceneGraphCommand):
    uids: list[str]

# Connection Commands:
@dataclass(frozen=True)
class RemoveConnectionsCommand(SceneGraphCommand):
    uids: list[str]
