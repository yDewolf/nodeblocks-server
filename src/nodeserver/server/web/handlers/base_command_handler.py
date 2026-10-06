from abc import ABC, abstractmethod

from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.providers.scene_worker_manager_protocol import ISceneWorkerManager
from nodeserver.server.protocols.session_protocols import SceneConnectionSession
from nodeserver.server.protocols.web.messages.base_client_command import BaseClientCommand

class BaseSceneCmdHandler(ABC):
    @property
    @abstractmethod
    def required_permission(self) -> ScenePermission:
        pass

    @abstractmethod
    async def handle(
        self, 
        message: BaseClientCommand,
        session: SceneConnectionSession,
        worker_manager: ISceneWorkerManager
    ):
        pass
