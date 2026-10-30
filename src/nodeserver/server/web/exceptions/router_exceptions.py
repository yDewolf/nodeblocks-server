from nodeserver.server.exceptions.server_exceptions import ServerDomainError
from nodeserver.server.web.routing.base_router import BaseRouter

from typing import Any, Optional


class ServerRouterError(ServerDomainError):
    def __init__(
        self,
        router_cls: type[BaseRouter],
        error_code: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(error_code, message, {"router_cls": router_cls, **(details or {})})


class CmdReponseMissingRequestId(ServerRouterError):
    def __init__(
        self,
        router_cls: type[BaseRouter],
        response_type: type
    ) -> None:
        super().__init__(
            router_cls,
            "CMD_RESPONSE_MISSING_REQUEST_ID", 
            f"A {response_type.__class__} response is missing its request id",
            {"response_type": response_type}
        )
