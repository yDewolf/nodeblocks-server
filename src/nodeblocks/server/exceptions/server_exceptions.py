
from typing import Any, Optional

from aiohttp import web

from nodeblocks.server.web.policies.base_policy import BaseWebPolicy


class ServerDomainError(Exception):
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}


class ServerPolicyError(ServerDomainError):
    def __init__(
        self,
        policy_cls: type[BaseWebPolicy],
        error_code: str,
        message: str,
        http_code: int = 400,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.http_status = http_code
        super().__init__(error_code, message, {"policy_cls": policy_cls, "http_code": http_code, **(details or {})})

