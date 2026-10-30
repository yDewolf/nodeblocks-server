
from typing import Any, Optional

from nodeserver.server.web.policies.base_policy import BaseWebPolicy


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
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(error_code, message, {"policy_cls": policy_cls, **(details or {})})

