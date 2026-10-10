from dataclasses import dataclass, field
import datetime
from typing import Any, Optional, Self
from aiohttp import web
import jwt
from nodeserver.protocols.helpers.uuid_utils import IDGenerator
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.server_env import SECRET_KEY


@dataclass(frozen=True)
class UserSession:
    user_id: str
    display_name: str = "Unindentified"

@dataclass(frozen=True)
class SceneSessionToken:
    sub: str # user id
    sid: str # scene id
    iat: int
    exp: int

    @classmethod
    def new(cls, user_id: str, scene_id: str, expires_in_hours: int = 1) -> Self:
        now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        return cls(
            sub=user_id,
            sid=scene_id,
            iat=now,
            exp=now + (expires_in_hours * 3600)
        )

    @classmethod
    def from_token_str(cls, token: str) -> Self:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return cls(**payload)

    def __str__(self) -> str:
        return jwt.encode(self.__dict__, SECRET_KEY, algorithm="HS256")

@dataclass
class SceneConnectionSession:
    token_payload: SceneSessionToken

    user: UserSession
    permissions: ScenePermission

    socket: web.WebSocketResponse
    connection_id: str = field(default_factory=lambda: IDGenerator.generate_generic_id(length=4))

    def has_permission(self, required: ScenePermission) -> bool:
        return required in self.permissions

    @property
    def scene_id(self): return self.token_payload.sid

    @property
    def id(self):
        return self.connection_id
