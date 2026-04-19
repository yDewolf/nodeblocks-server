from typing import Annotated, Any, Dict, Literal, Union
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from nodeserver.api.instance_states import InstanceStates, LoopStates
from nodeserver.api.web.websocket_protocol import EditorActionStatus, ServerMessages, WebsocketStatus
from nodeserver.networking.nodes.helpers.file.node_scene_dataclasses import SceneData

class BaseSocketModel(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True
    )


class SyncStatePayload(BaseSocketModel):
    instance_state: InstanceStates
    loop_state: LoopStates


class SrvHandshakeSuccess(BaseSocketModel):
    type: Literal[ServerMessages.HANDSHAKE_SYNC] = ServerMessages.HANDSHAKE_SYNC
    status: Literal[WebsocketStatus.CONNECTED]
    session: str
    type_data: Any

class SrvHandshakeError(BaseSocketModel):
    type: Literal[ServerMessages.HANDSHAKE_SYNC] = ServerMessages.HANDSHAKE_SYNC
    status: Literal[WebsocketStatus.DISCONNECTED, WebsocketStatus.ERROR]
    message: str

class SrvSyncAction(BaseSocketModel):
    type: Literal[ServerMessages.SYNC_ACTION] = ServerMessages.SYNC_ACTION
    action_statuses: Dict[str, EditorActionStatus]

class SrvSyncScene(BaseSocketModel):
    type: Literal[ServerMessages.SYNC_CLIENT_SCENE] = ServerMessages.SYNC_CLIENT_SCENE
    payload: SceneData

class SrvSyncState(BaseSocketModel):
    type: Literal[ServerMessages.SYNC_INSTANCE_STATE] = ServerMessages.SYNC_INSTANCE_STATE
    payload: SyncStatePayload


class SrvNodeOutput(BaseSocketModel):
    type: Literal[ServerMessages.NODE_OUTPUT] = ServerMessages.NODE_OUTPUT
    node_id: str
    value: dict[str, Any]

HandshakeMessage = Annotated[
    Union[SrvHandshakeSuccess, SrvHandshakeError], 
    Field(discriminator="status")
]

ServerMessage = Annotated[
    Union[HandshakeMessage, SrvSyncAction, SrvSyncScene, SrvSyncState, SrvNodeOutput],
    Field(discriminator="type")
]

ServerMessageAdapter = TypeAdapter(ServerMessage)
