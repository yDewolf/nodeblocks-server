from dataclasses import dataclass
import datetime
from typing import Any, Optional, Self
from aiohttp import web
import jwt
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.server_env import SECRET_KEY


@dataclass(frozen=True)
class UserSession:
    user_id: str
    display_name: str = "Unindentified"

@dataclass
class SceneConnectionSession:
    token_payload: SceneSessionToken

    user: UserSession
    permissions: ScenePermission

    socket: web.WebSocketResponse
    _token_str: Optional[str] = None

    def has_permission(self, required: ScenePermission) -> bool:
        return required in self.permissions

    @property
    def scene_id(self): return self.token_payload.sid
    
    @property
    def id(self): 
        if not self._token_str:
            self._token_str = str(self.token_payload)
        
        return self._token_str


@dataclass(frozen=True)
class SceneSessionToken:
    sub: str # user id
    sid: str # scene id
    iat: datetime.datetime
    exp: datetime.datetime

    @classmethod
    def new(cls, user_id: str, scene_id: str) -> Self:
        return cls(
            sub=user_id,
            sid=scene_id,
            iat=datetime.datetime.now(datetime.timezone.utc),
            exp=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        )

    @classmethod
    def from_token_str(cls, token: str) -> Self:
        payload = SessionUtils.validate_session_token(token)
        if not payload:
            raise Exception()
        
        return cls(**payload)

    def __str__(self) -> str:
        return jwt.encode(self.__dict__, SECRET_KEY, algorithm="HS256")


class SessionUtils:
    @staticmethod
    def validate_session_token(token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return payload

        except jwt.ExpiredSignatureError:
            return None

        except jwt.InvalidTokenError:
            return None
