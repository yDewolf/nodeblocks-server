
from dataclasses import dataclass, field
import datetime
from typing import Self

from aiohttp import web
import jwt

from nodeblocks.protocols.helpers.uuid_utils import IDGenerator
from nodeblocks.server.server_env import SERVER_ENV

@dataclass(frozen=True)
class ConnectionToken:
    iat: int
    exp: int

    @classmethod
    def new(cls, expires_in_hours: int = 3) -> Self:
        now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        return cls(
            iat=now,
            exp=now + (expires_in_hours * 3600)
        )

    @classmethod
    def from_token_str(cls, token: str) -> Self:
        payload = jwt.decode(token, SERVER_ENV.secret_key, algorithms=["HS256"])
        return cls(**payload)

    def __str__(self) -> str:
        return jwt.encode(self.__dict__, SERVER_ENV.secret_key, algorithm="HS256")

@dataclass
class ServerConnectionSession:
    socket: web.StreamResponse
    token_payload: ConnectionToken
    connection_id: str = field(default_factory=lambda: IDGenerator.generate_generic_id(length=4))

    @property
    def id(self):
        return self.connection_id
