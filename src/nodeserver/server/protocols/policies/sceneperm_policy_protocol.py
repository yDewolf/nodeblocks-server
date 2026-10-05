from abc import ABC, abstractmethod

from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.session_protocols import UserSession


class IScenePermPolicy(ABC):
    @abstractmethod
    async def get_default_scene_perms(self, scene_id: str) -> ScenePermission:
        pass
    
    @abstractmethod
    async def get_scene_permissions(self, user: UserSession, scene_id: str) -> ScenePermission:
        pass

    @abstractmethod
    async def update_scene_permissions(self, user: UserSession, target_user: str, scene_id: str, perms: ScenePermission):
        pass
