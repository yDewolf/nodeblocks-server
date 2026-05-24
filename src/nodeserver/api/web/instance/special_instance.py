from pydantic import BaseModel

from nodeserver.api.instance.instance_runtime import InstanceRuntime
from nodeserver.api.instance.server_instance import ServerInstance
from nodeserver.api.web.session.user_session import UserSession
from nodeserver.api.web.session.user_workspace import UserWorkspace
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import TypeFileReader

class WorkspaceAwareInput(BaseModel):
    class Config:
        arbitrary_types_allowed=True
    
    _workspace: UserWorkspace

class WebsocketInstanceRuntime(InstanceRuntime):
    _user_workspace: UserWorkspace
    def __init__(self, _user_workspace: UserWorkspace):
        super().__init__()
        self._user_workspace = _user_workspace

    def insert_extra_input_data(self, node_inputs: BaseModel) -> None:
        super().insert_extra_input_data(node_inputs)
        if isinstance(node_inputs, WorkspaceAwareInput):
            node_inputs._workspace = self._user_workspace

class WsServerInstance(ServerInstance):
    def __init__(self, related_session: UserSession, types: TypeFileReader | None = None):
        super().__init__(types)

        self._runtime = WebsocketInstanceRuntime(related_session.workspace)
