from typing import List, Dict, Union, Literal, Annotated
from pydantic import Field, TypeAdapter

from nodeserver.api.web.requests.websocket_requests import BaseSocketModel
from nodeserver.api.web.websocket_protocol import SceneActionTypes
from nodeserver.networking.nodes.helpers.file.node_scene_dataclasses import ConnectionSceneData, NodeSceneData

# Node Action Payloads
class NodeActionAddUpdate(BaseSocketModel):
    action: Literal[SceneActionTypes.ADD, SceneActionTypes.UPDATE]
    action_data: Dict[str, NodeSceneData] 

class NodeActionRemove(BaseSocketModel):
    action: Literal[SceneActionTypes.REMOVE]
    uids: List[str]

NodeActionPayload = Annotated[
    Union[NodeActionAddUpdate, NodeActionRemove], 
    Field(discriminator="action")
]
NodeActionPayloadAdapter = TypeAdapter(NodeActionPayload)

# Connection Action Payloads
class ConnectionActionAddUpdate(BaseSocketModel):
    action: Literal[SceneActionTypes.ADD, SceneActionTypes.UPDATE]
    action_data: Dict[str, ConnectionSceneData]

class ConnectionActionRemove(BaseSocketModel):
    action: Literal[SceneActionTypes.REMOVE]
    uids: List[str]

ConnectionActionPayload = Annotated[
    Union[ConnectionActionAddUpdate, ConnectionActionRemove], 
    Field(discriminator="action")
]

ConnActionPayloadAdapter = TypeAdapter(ConnectionActionPayload)