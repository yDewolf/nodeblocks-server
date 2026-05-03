from typing import Annotated, Any, Dict, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from nodeserver.api.instance.instance_states import InstanceStates, LoopStates
from nodeserver.api.web.requests.base_requests import BaseSocketModel
from nodeserver.api.web.requests.notification_requests import ServerNotification, ServerSyncNotifications
from nodeserver.api.web.websocket_protocol import EditorActionStatus, ServerMessages, WebsocketStatus
from nodeserver.wrapper.nodes.helpers.file.node_scene_dataclasses import SceneData


class SyncStatePayload(BaseSocketModel):
    instance_state: InstanceStates
    loop_state: LoopStates


class SrvHandshakeSuccess(BaseSocketModel):
    type: Literal[ServerMessages.HANDSHAKE_SYNC] = ServerMessages.HANDSHAKE_SYNC
    status: Literal[WebsocketStatus.CONNECTED]
    session: str
    type_data: Any
    reconnection: bool = False

class SrvHandshakeError(BaseSocketModel):
    type: Literal[ServerMessages.HANDSHAKE_SYNC] = ServerMessages.HANDSHAKE_SYNC
    status: Literal[WebsocketStatus.DISCONNECTED, WebsocketStatus.ERROR]
    message: str

class SrvSyncAction(BaseSocketModel):
    type: Literal[ServerMessages.SYNC_ACTION] = ServerMessages.SYNC_ACTION
    action_statuses: Dict[str, EditorActionStatus]

class SrvSyncScene(BaseSocketModel):
    type: Literal[ServerMessages.SYNC_CLIENT_SCENE] = ServerMessages.SYNC_CLIENT_SCENE
    payload: Optional[SceneData]

class SrvSyncState(BaseSocketModel):
    type: Literal[ServerMessages.SYNC_INSTANCE_STATE] = ServerMessages.SYNC_INSTANCE_STATE
    payload: SyncStatePayload

class SrvSyncFiles(BaseSocketModel):
    type: Literal[ServerMessages.SYNC_FILES] = ServerMessages.SYNC_FILES


class SrvNodeOutput(BaseSocketModel):
    type: Literal[ServerMessages.NODE_OUTPUT] = ServerMessages.NODE_OUTPUT
    node_id: str
    value: dict[str, Any]

HandshakeMessage = Annotated[
    Union[SrvHandshakeSuccess, SrvHandshakeError], 
    Field(discriminator="status")
]

ServerMessage = Annotated[
    Union[HandshakeMessage, ServerNotification, ServerSyncNotifications, SrvSyncAction, SrvSyncScene, SrvSyncState, SrvNodeOutput, SrvSyncFiles],
    Field(discriminator="type")
]

ServerMessageAdapter = TypeAdapter(ServerMessage)