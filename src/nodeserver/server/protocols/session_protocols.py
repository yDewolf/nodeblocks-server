from dataclasses import dataclass
import datetime
from typing import Optional
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
    token: Optional[str]
    scene_id: str

    user: UserSession
    permissions: ScenePermission

    socket: web.WebSocketResponse

    def has_permission(self, required: ScenePermission) -> bool:
        return required in self.permissions


class SessionUtils:
    @staticmethod
    def create_session_token(user_id: str, scene_id: str):
        payload = {
            "sub": user_id,
            "sid": scene_id,
            "iat": datetime.datetime.now(datetime.timezone.utc),
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    @staticmethod
    def validate_session_token(token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return payload

        except jwt.ExpiredSignatureError:
            return None

        except jwt.InvalidTokenError:
            return None
