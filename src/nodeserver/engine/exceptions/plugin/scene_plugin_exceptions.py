from typing import Any, Optional
from nodeserver.engine.exceptions.base_exceptions import EngineDomainError

class PluginSceneDomainException(EngineDomainError):
    def __init__(
        self,
        error_code: str,
        message: str,
        scene_id: Optional[str] = None,
        extra_details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            error_code,
            message,
            {"scene_id": scene_id, **(extra_details or {})}
        )

class IncompatibleSceneDependency(PluginSceneDomainException):
    def __init__(
        self,
        scene_id: str,
        dependency_id: str,
        target_version: str,
        current_version: str
    ) -> None:
        super().__init__(
            "INCOMPATIBLE_DEPENDENCY_VERSION",
            f"Scene '{scene_id}' is not compatible with {dependency_id}'s version ({current_version}). Requirement: {target_version}",
            scene_id, {
                "dependency_id": dependency_id,
                "target_version": target_version, 
                "current_version": current_version
            }
        )


class MissingSceneDependency(PluginSceneDomainException):
    def __init__(
        self,
        scene_id: str,
        loaded_plugins: list[str],
        scene_dependencies: dict[str, str]
    ) -> None:
        missing_dependencies: list[str] = [
            dependency for dependency in scene_dependencies
            if not dependency in loaded_plugins
        ]
        super().__init__(
            "SCENE_MISSING_DEPENDENCY",
            f"Scene '{scene_id}' dependencies weren't loaded. Missing dependencies: {missing_dependencies}",
            scene_id, {"loaded_plugins": loaded_plugins, "dependencies": scene_dependencies, "missing_dependencies": missing_dependencies}
        )
