from abc import ABC, abstractmethod
from typing import Protocol

from nodeblocks.protocols.manifest.node.node_graph import SceneData
from nodeblocks.server.protocols.permission.scene_permissions import ScenePermission
from nodeblocks.server.protocols.scene_list_protocol import ListedScenePerms
from nodeblocks.server.protocols.session_protocols import SceneSessionToken, UserSession


class IScenePermPolicy(ABC):
    @abstractmethod
    async def create_scene_token(self, user: UserSession, scene_id: str) -> SceneSessionToken:
        pass

    @abstractmethod
    async def get_default_scene_perms(self, scene_id: str) -> ScenePermission:
        pass
    
    @abstractmethod
    async def get_scene_permissions(self, user: UserSession, scene_id: str) -> ScenePermission:
        pass

    @abstractmethod
    async def get_all_scene_perms(self, user: UserSession, scene_id: str) -> ListedScenePerms:
        pass

    @abstractmethod
    async def update_scene_permissions(self, user: UserSession, target_user: str, scene_id: str, perms: ScenePermission):
        pass

    @abstractmethod
    async def update_default_scene_perms(self, user: UserSession, scene_id: str, perms: ScenePermission):
        pass

    @abstractmethod
    async def get_scene_data(self, user: UserSession, scene_id: str) -> SceneData:
        pass
