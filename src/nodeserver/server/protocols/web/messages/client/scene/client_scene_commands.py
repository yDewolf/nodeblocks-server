from typing import Annotated, Literal, Union

from pydantic import Field

from nodeserver.protocols.manifest.node.node_graph import SceneData
from nodeserver.server.protocols.web.messages.client.base_client_command import BaseClientCommand
from nodeserver.server.protocols.web.messages.client.base_client_command import CommandGroups
from nodeserver.server.protocols.web.messages.client.client_message_enums import ClientSceneCommandTypes


class ClientSceneCommand(BaseClientCommand):
    cmd_group: Literal[CommandGroups.SCENE]
    type: ClientSceneCommandTypes


class ClientLoadSceneCmd(ClientSceneCommand):
    type: Literal[ClientSceneCommandTypes.LOAD_SCENE]
    payload: SceneData


SceneCommandAdapter = Annotated[
    Union[ClientLoadSceneCmd, ],
    Field(discriminator="type")
]
