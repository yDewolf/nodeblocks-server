from abc import abstractmethod
from typing import Protocol

from nodeserver.engine.protocols.providers.scene_provider import ISceneDataProvider
from nodeserver.engine.protocols.providers.scene_state_provider import ISceneStateProvider
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.scene_list_protocol import ListedScene


class IServerSceneProvider(Protocol):
    @abstractmethod
    def setup(self): pass

    @abstractmethod
    def get_listed_scenes(self) -> list[ListedScene]: 
        pass

    @abstractmethod
    def get_default_scene_perms(self, scene_uid: str) -> ScenePermission:
        pass

    @abstractmethod
    def get_scene_permissions(self, scene_uid: str, user_id: str) -> ScenePermission: 
        pass

    @abstractmethod
    def update_scene_permissions(self, scene_uid: str, user_id: str, permissions: ScenePermission):
        pass

