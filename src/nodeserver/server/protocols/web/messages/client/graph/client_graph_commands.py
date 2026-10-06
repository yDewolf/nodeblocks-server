from typing import Annotated, Literal, Union

from pydantic import Field

from nodeserver.server.protocols.web.messages.client.base_client_command import BaseClientCommand, CommandGroups
from nodeserver.server.protocols.web.messages.client.client_message_enums import ClientGraphCommandTypes
from nodeserver.server.protocols.web.messages.client.graph.graph_action_payloads import ConnActionPayloadAdapter, NodeActionPayloadAdapter


class ClientGraphCommand(BaseClientCommand):
    cmd_group: Literal[CommandGroups.GRAPH]
    type: ClientGraphCommandTypes


class NodeGraphCommand(ClientGraphCommand):
    type: Literal[ClientGraphCommandTypes.NODE]
    payload: NodeActionPayloadAdapter

class ConnGraphCommand(ClientGraphCommand):
    type: Literal[ClientGraphCommandTypes.CONN]
    payload: ConnActionPayloadAdapter


SceneGraphCommandAdapter = Annotated[
    Union[NodeGraphCommand, ConnGraphCommand],
    Field(discriminator="type")
]
