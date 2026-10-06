from typing import Annotated, Union

from pydantic import Field, TypeAdapter

from nodeserver.server.protocols.web.base_socket_model import BaseSocketModel
from nodeserver.server.protocols.web.messages.graph.client_graph_commands import SceneGraphCommandAdapter
from nodeserver.server.protocols.web.messages.scene.client_scene_commands import SceneCommandAdapter
from nodeserver.server.protocols.web.messages.scene.scene_runtime_commands import ExecutionCommandAdapter

ClientCommandAdapter = Annotated[
    Union[
        SceneGraphCommandAdapter, SceneCommandAdapter, ExecutionCommandAdapter
    ], # TODO: implementar notificações aqui
    Field(discriminator="cmd_group")
]

ClientCommandPayloadAdapter = TypeAdapter(ClientCommandAdapter)

class ClientMessageWrapper(BaseSocketModel):
    payload: ClientCommandAdapter
