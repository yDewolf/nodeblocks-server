
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.providers.scene_worker_manager_protocol import ISceneWorkerManager
from nodeserver.server.protocols.session_protocols import SceneConnectionSession
from nodeserver.server.protocols.web.messages.base_client_command import BaseClientCommand
from nodeserver.server.web.handlers.base_command_handler import BaseSceneCmdHandler

# TODO:
class GraphCommandHandler(BaseSceneCmdHandler):
    @property
    def required_permission(self) -> ScenePermission:
        return ScenePermission.EDIT

    def handle(
        self, 
        message: BaseClientCommand, 
        session: SceneConnectionSession, 
        worker_manager: ISceneWorkerManager
    ):
        pass
