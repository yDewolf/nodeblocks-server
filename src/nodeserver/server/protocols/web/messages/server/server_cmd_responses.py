from enum import StrEnum
from pydantic import Field
from typing import Annotated, Literal, Optional, Union

from nodeserver.protocols.manifest.node.node_graph import SceneData
from nodeserver.server.protocols.web.base_socket_model import BaseSocketModel
from nodeserver.engine.workers.protocols.ipc_protocol import CmdStatus
from nodeserver.engine.workers.scene.protocols.scene_worker_states import SceneWorkerExecutionMode, SceneWorkerExecutionState

# TODO: criar models para usar isso aqui como
# discriminator do response_payload em BaseServerCmdResponse
class ServerResponseTypes(StrEnum):
    SCENE_WORKER = "scene_worker" # generic
    
    EXECUTION_STATE_SYNC = "execution_state_sync"
    ADD_NODE = "add_node"
    ADD_CONN = "add_conn"
    GET_SCENE_DATA = "get_scene_data"
    SAVE_SCENE = "save_scene"

class CommandResponsePayload(BaseSocketModel):
    type: ServerResponseTypes
    
    request_id: str
    status: CmdStatus

# TODO: move these to other file
class GenericCommandPayload(CommandResponsePayload):
    type: Literal[ServerResponseTypes.SCENE_WORKER] = ServerResponseTypes.SCENE_WORKER

class ExecutionStateSyncPayload(CommandResponsePayload):
    type: Literal[ServerResponseTypes.EXECUTION_STATE_SYNC] = ServerResponseTypes.EXECUTION_STATE_SYNC
    state: SceneWorkerExecutionState
    mode: SceneWorkerExecutionMode

class AddNodePayload(CommandResponsePayload):
    type: Literal[ServerResponseTypes.ADD_NODE] = ServerResponseTypes.ADD_NODE
    nodes: Optional[list[str]]    

class AddConnPayload(CommandResponsePayload):
    type: Literal[ServerResponseTypes.ADD_CONN] = ServerResponseTypes.ADD_CONN
    conns: Optional[list[str]]

class GetSceneDataPayload(CommandResponsePayload):
    type: Literal[ServerResponseTypes.GET_SCENE_DATA] = ServerResponseTypes.GET_SCENE_DATA
    scene_data: Optional[SceneData]

class SaveScenePayload(CommandResponsePayload):
    type: Literal[ServerResponseTypes.SAVE_SCENE] = ServerResponseTypes.SAVE_SCENE


CmdResponsePayloadAdapter = Annotated[
    Union[
        GenericCommandPayload, ExecutionStateSyncPayload, 
        AddConnPayload, AddNodePayload, 
        GetSceneDataPayload, SaveScenePayload
    ],
    Field(discriminator="type")
]