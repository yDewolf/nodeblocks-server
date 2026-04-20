import jwt
import datetime

from nodeserver.api.utils.env_variables import SECRET_KEY


class UserSession:
    token: str
    instance_id: str

    is_disconnected: bool
    disconnected_at: datetime.datetime

    def __init__(self, token: str, instance_id: str) -> None:
        self.token = token
        self.instance_id = instance_id
        self.is_disconnected = False

    def mark_disconnected(self):
        self.is_disconnected = True
        self.disconnected_at = datetime.datetime.now(datetime.timezone.utc)

    def mark_connected(self):
        self.is_disconnected = False


def create_session_token(user_id: str, instance_id: str):
    payload = {
        "sub": user_id,
        "iid": instance_id,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def validate_session_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload

    except jwt.ExpiredSignatureError:
        return None

    except jwt.InvalidTokenError:
        return None