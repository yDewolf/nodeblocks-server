from typing import Annotated, Any, Dict, Literal, Optional, Union
from pydantic import Field
from nodeserver.api.instance.instance_states import InstanceStates, LoopStates
from nodeserver.api.web.requests.base_requests import BaseSocketModel
from nodeserver.api.web.requests.notification_requests import ServerSyncNotifications
from nodeserver.api.web.websocket_protocol import EditorActionStatus, ServerMessages, WebsocketStatus
from nodeserver.wrapper.metadata.metadata_header import Metadata, MetadataVersion
from nodeserver.wrapper.nodes.helpers.file.node_scene_dataclasses import SceneData
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import TypeFile


class SyncStatePayload(BaseSocketModel):
    instance_state: InstanceStates
    loop_state: LoopStates

class SrvMetadataUpdated(BaseSocketModel):
    type: Literal[ServerMessages.METADATA_UPDATED] = ServerMessages.METADATA_UPDATED
    metadata_version: MetadataVersion

class SrvVersionSync(BaseSocketModel):
    type: Literal[ServerMessages.SYNC_VERSIONS] = ServerMessages.SYNC_VERSIONS
    types: Optional[TypeFile]
    metadata: Optional[Metadata] # FIXME: Don't send full metadata, client should request it

class SrvHandshakeSuccess(BaseSocketModel):
    type: Literal[ServerMessages.HANDSHAKE_SYNC] = ServerMessages.HANDSHAKE_SYNC
    status: Literal[WebsocketStatus.CONNECTED]
    session: str

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

BaseServerMessages = Annotated[
    Union[
        HandshakeMessage, SrvVersionSync, SrvMetadataUpdated,
        ServerSyncNotifications, SrvSyncAction, SrvSyncScene, SrvSyncState, SrvNodeOutput, SrvSyncFiles
    ],
    Field(discriminator="type")
]