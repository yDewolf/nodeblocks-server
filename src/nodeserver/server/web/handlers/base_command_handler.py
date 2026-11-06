from abc import ABC, abstractmethod

from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.providers.scene_worker_manager_protocol import ISceneWorkerManager
from nodeserver.server.protocols.session_protocols import SceneConnectionSession
from nodeserver.server.protocols.web.messages.client.base_client_command import BaseClientCommand
from nodeserver.server.protocols.web.messages.client.client_message_wrapper import ClientCommandAdapter

class BaseSceneCmdHandler(ABC):
    @property
    @abstractmethod
    def required_permission(self) -> ScenePermission:
        pass

    
    def required_permission_for(self, cmd: ClientCommandAdapter) -> ScenePermission:
        return self.required_permission


    @abstractmethod
    async def handle(
        self, 
        message: BaseClientCommand,
        session: SceneConnectionSession,
        worker_manager: ISceneWorkerManager
    ):
        pass
