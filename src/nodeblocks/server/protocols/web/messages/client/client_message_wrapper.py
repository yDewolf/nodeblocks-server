from typing import Annotated, Union

from pydantic import Field, TypeAdapter

from nodeblocks.server.protocols.web.base_socket_model import BaseSocketModel
from nodeblocks.server.protocols.web.messages.client.graph.client_graph_commands import SceneGraphCommandAdapter
from nodeblocks.server.protocols.web.messages.client.scene.client_scene_commands import SceneCommandAdapter
from nodeblocks.server.protocols.web.messages.client.scene.scene_runtime_commands import ExecutionCommandAdapter

ClientCommandAdapter = Annotated[
    Union[
        SceneGraphCommandAdapter, SceneCommandAdapter, ExecutionCommandAdapter
    ],
    Field(discriminator="cmd_group")
]

ClientCommandPayloadAdapter = TypeAdapter(ClientCommandAdapter)

class ClientMessageWrapper(BaseSocketModel):
    payload: ClientCommandAdapter
