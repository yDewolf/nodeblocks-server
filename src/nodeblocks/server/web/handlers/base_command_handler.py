from abc import ABC, abstractmethod

from nodeblocks.server.protocols.permission.scene_permissions import ScenePermission
from nodeblocks.server.protocols.providers.scene_worker_manager_protocol import ISceneWorkerManager
from nodeblocks.server.protocols.session_protocols import SceneConnectionSession
from nodeblocks.server.protocols.web.messages.client.base_client_command import BaseClientCommand
from nodeblocks.server.protocols.web.messages.client.client_message_wrapper import ClientCommandAdapter

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
