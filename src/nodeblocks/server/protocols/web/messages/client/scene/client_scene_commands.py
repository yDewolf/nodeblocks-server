from typing import Annotated, Literal, Union

from pydantic import Field

from nodeblocks.protocols.manifest.node.node_graph import SceneData
from nodeblocks.server.protocols.web.messages.client.base_client_command import BaseClientCommand
from nodeblocks.server.protocols.web.messages.client.base_client_command import CommandGroups
from nodeblocks.server.protocols.web.messages.client.client_message_enums import ClientSceneCommandTypes


class ClientSceneCommand(BaseClientCommand):
    cmd_group: Literal[CommandGroups.SCENE]
    type: ClientSceneCommandTypes


class ClientLoadSceneCmd(ClientSceneCommand):
    type: Literal[ClientSceneCommandTypes.LOAD_SCENE]
    payload: SceneData

class ClientSaveSceneCmd(ClientSceneCommand):
    type: Literal[ClientSceneCommandTypes.SAVE_SCENE]

class ClientSetSceneAutosaveCmd(ClientSceneCommand):
    type: Literal[ClientSceneCommandTypes.SET_SCENE_AUTOSAVE]
    autosave: bool

class ClientGetSceneDataCmd(ClientSceneCommand):
    type: Literal[ClientSceneCommandTypes.GET_SCENE_DATA]


SceneCommandAdapter = Annotated[
    Union[ClientLoadSceneCmd, ClientSaveSceneCmd, ClientGetSceneDataCmd, ClientSetSceneAutosaveCmd],
    Field(discriminator="type")
]
