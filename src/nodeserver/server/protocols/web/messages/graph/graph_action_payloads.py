from typing import Annotated, Literal, Union

from pydantic import Field

from nodeserver.protocols.manifest.node.node_graph import ConnectionSceneData, NodeSceneData
from nodeserver.server.protocols.web.base_socket_model import BaseSocketModel
from nodeserver.server.protocols.web.messages.client_message_enums import GraphActionTypes

# -- Node Actions:

# Add or update a node
class NodeAddUpdateAction(BaseSocketModel):
    action: Literal[GraphActionTypes.ADD, GraphActionTypes.UPDATE]
    action_data: dict[str, NodeSceneData] # node_uid -> data

class NodeRemoveAction(BaseSocketModel):
    action: Literal[GraphActionTypes.REMOVE]
    uids: list[str]

NodeActionPayloadAdapter = Annotated[
    Union[NodeAddUpdateAction, NodeRemoveAction],
    Field(discriminator="action")
]


# -- Connection Actions:

class ConnAddUpdateAction(BaseSocketModel):
    action: Literal[GraphActionTypes.ADD, GraphActionTypes.UPDATE]
    action_data: dict[str, ConnectionSceneData]

class ConnRemoveAction(BaseSocketModel):
    action: Literal[GraphActionTypes.REMOVE]
    uids: list[str]

ConnActionPayloadAdapter = Annotated[
    Union[ConnAddUpdateAction, ConnRemoveAction],
    Field(discriminator="action")
]
