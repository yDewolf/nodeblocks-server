from typing import Any

from nodeserver.server.exceptions.server_exceptions import ServerPolicyError
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.web.policies.base_policy import BaseWebPolicy


class ScenePermPolicyError(ServerPolicyError):
    def __init__(
        self, 
        policy_cls: type[BaseWebPolicy], 
        error_code: str, 
        message: str, 
        details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(policy_cls, error_code, message, details)


class SceneUnauthorizedActionError(ScenePermPolicyError):
    def __init__(
        self, 
        policy_cls: type[BaseWebPolicy], 
        action: str,
        actor_id: str,
        actor_perms: ScenePermission,
        required_perms: ScenePermission,
    ) -> None:
        super().__init__(
            policy_cls, 
            "UNAUTHORIZED_SCENE_ACTION", 
            f"User {actor_id} must have permission level: {required_perms} to perform {action} action. Actor permissions: {actor_perms}", 
            {"actor_id": actor_id, "actor_perms": actor_perms, "required_perms": required_perms, "action": action}
        )

class SceneNotFoundError(ScenePermPolicyError):
    def __init__(
        self, 
        policy_cls: type[BaseWebPolicy], 
        scene_id: str
    ) -> None:
        super().__init__(
            policy_cls, 
            "SCENE_NOT_FOUND", 
            f"Couldn't find scene data for scene: {scene_id}",
            {"scene_id": scene_id}
        )
