from abc import abstractmethod
from typing import Protocol

from aiohttp import web

from nodeserver.server.protocols.session_protocols import UserSession


class IAuthPolicy(Protocol):
    @abstractmethod
    async def authenticate(self, request: web.Request) -> UserSession:
        pass
