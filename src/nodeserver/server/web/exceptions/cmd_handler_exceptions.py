from typing import Any, Optional

from nodeserver.server.web.handlers.base_command_handler import BaseSceneCmdHandler


class ServerCmdHandlerError(Exception):
    def __init__(
        self,
        handler_cls: type[BaseSceneCmdHandler],
        error_code: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            error_code, 
            message, 
            {"handler_cls": handler_cls, **(details or {})}
        )


class CmdDispatchNotImplemented(ServerCmdHandlerError):
    def __init__(
        self,
        handler_cls: type[BaseSceneCmdHandler],
        cmd_type: type
    ) -> None:
        super().__init__(
            handler_cls,
            "COMMAND_DISPATCH_NOT_IMPLEMENTED", 
            f"Command {cmd_type.__name__} is not implemented in {handler_cls.__name__}", 
            {"cmd_type": cmd_type}
        )
