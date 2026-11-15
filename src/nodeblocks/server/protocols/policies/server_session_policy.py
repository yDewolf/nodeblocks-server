from abc import abstractmethod
from asyncio import Protocol

from aiohttp import web

from nodeblocks.server.protocols.policies.auth_policy_protocol import IAuthPolicy
from nodeblocks.server.protocols.session.server_connection import ConnectionToken


class IServerSessionPolicy(Protocol):
    @abstractmethod
    async def create_token(self, request: web.Request, auth_policy: IAuthPolicy) -> ConnectionToken:
        pass
