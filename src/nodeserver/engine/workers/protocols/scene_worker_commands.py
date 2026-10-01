from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Optional

from nodeserver.engine.protocols.ipc_protocol import IPCCommand
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData, SceneData
from nodeserver.protocols.manifest.structs.scene_structs import Vector2


class GraphExecutionModes(StrEnum):
    FULL_GRAPH = "full_graph"
    GRAPH_STEP = "graph_step"
    CONTINUOUS = "continuous"


class IPCSceneWorkerCommand(IPCCommand):
    pass


# Graph Execution
@dataclass(frozen=True)
class StopWorkerCommand(IPCSceneWorkerCommand):
    pass


@dataclass(frozen=True)
class ExecuteGraphCommand(IPCSceneWorkerCommand):
    mode: GraphExecutionModes


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
