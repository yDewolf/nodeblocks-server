from typing import Annotated, Literal, Union
from pydantic import Field
from pydantic import TypeAdapter

from nodeserver.api.instance.instance_states import InstanceCommands, InstanceStates, LoopStates
from nodeserver.api.web.requests.action_requests import ConnectionActionPayload, NodeActionPayload
from nodeserver.api.web.requests.base_requests import BaseSocketModel
from nodeserver.api.web.websocket_protocol import ClientMessages
from nodeserver.wrapper.nodes.helpers.file.node_scene_dataclasses import SceneData

class InstanceCommandPayload(BaseSocketModel):
    action: InstanceCommands

class InstanceStatePayload(BaseSocketModel):
    state: InstanceStates

class LoopStatePayload(BaseSocketModel):
    state: LoopStates


# Client Messages
class MsgNodeAction(BaseSocketModel):
    type: Literal[ClientMessages.NODE_ACTION]
    payload: NodeActionPayload
    action_uid: str

class MsgConnectionAction(BaseSocketModel):
    type: Literal[ClientMessages.CONNECTION_ACTION]
    payload: ConnectionActionPayload
    action_uid: str

class MsgInstanceState(BaseSocketModel):
    type: Literal[ClientMessages.SET_INSTANCE_STATE]
    payload: InstanceStatePayload

class MsgLoopState(BaseSocketModel):
    type: Literal[ClientMessages.SET_INSTANCE_LOOP_STATE]
    payload: LoopStatePayload

class MsgLoadScene(BaseSocketModel):
    type: Literal[ClientMessages.LOAD_SCENE]
    payload: SceneData

class MsgInstanceCommand(BaseSocketModel):
    type: Literal[ClientMessages.INSTANCE_COMMAND]
    payload: InstanceCommandPayload

class MsgSimple(BaseSocketModel):
    type: Literal[ClientMessages.SYNC_CLIENT_SCENE]


ClientCommand = Annotated[
    Union[
        MsgNodeAction, MsgConnectionAction, MsgInstanceState, 
        MsgLoopState, MsgLoadScene, MsgInstanceCommand, MsgSimple
    ],
    Field(discriminator="type")
]

ClientCommandAdapter = TypeAdapter(ClientCommand)