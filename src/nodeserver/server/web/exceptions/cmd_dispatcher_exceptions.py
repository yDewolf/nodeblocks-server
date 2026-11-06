
from typing import Any, Optional

from nodeserver.server.exceptions.server_exceptions import ServerDomainError
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission


class ServerCmdDispatchError(ServerDomainError):
    def __init__(
        self,
        error_code: str,
        message: str,
        cmd_uid: Optional[str],
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.cmd_uid = cmd_uid
        super().__init__(
            error_code, 
            message, 
            {"cmd_uid": cmd_uid, **(details or {})}
        )

class UnknownCommandError(ServerCmdDispatchError):
    def __init__(
        self,
        cmd_uid: Optional[str],
        errors: Optional[list]
    ) -> None:
        super().__init__(
            "UNKNOWN_COMMAND_ERROR", 
            "Invalid command format", 
            cmd_uid,
            {"errors": errors}
        )

class UnimplementedCommandError(ServerCmdDispatchError):
    def __init__(
        self,
        cmd_group: str,
        cmd_uid: Optional[str],
    ) -> None:
        super().__init__(
            "UNIMPLEMENTED_COMMAND_ERROR", 
            f"No Handler registered for command group: {cmd_group}", 
            cmd_uid,
            {"cmd_group": cmd_group}
        )

class UnauthorizedCommandUsage(ServerCmdDispatchError):
    def __init__(
        self,
        cmd_type: str,
        cmd_uid: Optional[str],
        required_perms: ScenePermission,
        actor_perms: ScenePermission
    ) -> None:
        super().__init__(
            "UNAUTHORIZED_COMMAND_USAGE", 
            f"User doesn't have permission to use cmd: {cmd_type}. User Perms: {actor_perms}; Required: {required_perms}", 
            cmd_uid,
            {"required_perms": required_perms, "actor_perms": actor_perms}
        )
