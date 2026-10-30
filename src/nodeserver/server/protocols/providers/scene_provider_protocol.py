from abc import abstractmethod
from typing import Optional, Protocol

from nodeserver.engine.protocols.providers.scene_provider import ISceneDataProvider
from nodeserver.protocols.manifest.node.node_graph import SceneData
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.scene_list_protocol import ListedScene, ListedScenePerms


class IServerSceneProvider(Protocol):
    @abstractmethod
    def setup(self): pass

    @abstractmethod
    def create_scene(self, scene_id: str, author_id: str):
        pass

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
    def get_all_scene_perms(self, scene_uid: str) -> ListedScenePerms:
        pass


    @abstractmethod
    def update_scene_permissions(self, scene_uid: str, permissions: ScenePermission, user_id: Optional[str] = None):
        pass

    
    @abstractmethod
    def load_scene_data(self, scene_uid: str) -> Optional[SceneData]:
        pass

    @abstractmethod
    def save_scene_data(self, scene_data: SceneData):
        pass
