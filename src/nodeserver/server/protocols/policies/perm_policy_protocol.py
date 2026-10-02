from abc import ABC, abstractmethod
from aiohttp import web

from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.session_protocols import UserSession


class BasePermissionPolicy(ABC):
    @abstractmethod
    async def authenticate(self, request: web.Request) -> UserSession:
        pass

    @abstractmethod
    async def get_scene_permissions(self, user: UserSession, scene_id: str) -> ScenePermission:
        pass


class DevPermissionPolicy(BasePermissionPolicy):
    async def authenticate(self, request: web.Request) -> UserSession:
        user_id = request.query.get("user_id", "dev_user")
        return UserSession(user_id=user_id, display_name=f"User-{user_id}")

    async def get_scene_permissions(self, user: UserSession, scene_id: str) -> ScenePermission:
        return ScenePermission.ALL
