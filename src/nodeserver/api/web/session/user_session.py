from typing import Optional
import jwt
import datetime

from nodeserver.api.utils.env_variables import SECRET_KEY
from nodeserver.api.web.session.user_workspace import UserWorkspace

class UserSession:
    token: Optional[str]
    user_id: str
    
    workspace: UserWorkspace

    is_disconnected: bool
    disconnected_at: datetime.datetime

    def __init__(self, token: Optional[str], user_id: str) -> None:
        self.token = token
        self.user_id = user_id
        self.workspace = UserWorkspace.create(self.user_id)
        self.is_disconnected = False

    def mark_disconnected(self):
        self.is_disconnected = True
        self.disconnected_at = datetime.datetime.now(datetime.timezone.utc)

    def mark_connected(self):
        self.is_disconnected = False


class SessionUtils:
    @staticmethod
    def create_session_token(user_id: str, instance_id: str):
        payload = {
            "sub": user_id,
            "iid": instance_id,
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
