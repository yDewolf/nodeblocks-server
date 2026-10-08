from enum import StrEnum
from pydantic import Field
from typing import Annotated, Literal, Optional, Union

from nodeserver.server.protocols.web.base_socket_model import BaseSocketModel
from nodeserver.engine.workers.protocols.ipc_protocol import CmdStatus
from nodeserver.engine.workers.scene.protocols.scene_worker_states import SceneWorkerExecutionMode, SceneWorkerExecutionState

# TODO: criar models para usar isso aqui como
# discriminator do response_payload em BaseServerCmdResponse
class ServerResponseTypes(StrEnum):
    SCENE_WORKER = "scene_worker" # generic
    
    EXECUTION_STATE_CHECK = "execution_state_check"
    ADD_NODE = "add_node"
    ADD_CONN = "add_conn"

class CommandResponsePayload(BaseSocketModel):
    type: ServerResponseTypes
    
    request_id: str
    status: CmdStatus

# TODO: move these to other file
class GenericCommandPayload(CommandResponsePayload):
    type: Literal[ServerResponseTypes.SCENE_WORKER] = ServerResponseTypes.SCENE_WORKER

class ExecutionCheckPayload(CommandResponsePayload):
    type: Literal[ServerResponseTypes.EXECUTION_STATE_CHECK] = ServerResponseTypes.EXECUTION_STATE_CHECK
    state: SceneWorkerExecutionState
    mode: SceneWorkerExecutionMode

class AddNodePayload(CommandResponsePayload):
    type: Literal[ServerResponseTypes.ADD_NODE] = ServerResponseTypes.ADD_NODE
    nodes: Optional[list[str]]    

class AddConnPayload(CommandResponsePayload):
    type: Literal[ServerResponseTypes.ADD_CONN] = ServerResponseTypes.ADD_CONN
    conns: Optional[list[str]]


CmdResponsePayloadAdapter = Annotated[
    Union[GenericCommandPayload, ExecutionCheckPayload, AddConnPayload, AddNodePayload],
    Field(discriminator="type")
]