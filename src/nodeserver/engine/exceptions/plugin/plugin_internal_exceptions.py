from pathlib import Path

from nodeserver.engine.exceptions.base_exceptions import EngineDomainError

from typing import Any, Optional

# Exceptions that aren't caused by the plugin's developer

class PluginDomainException(EngineDomainError):
    def __init__(
        self,
        error_code: str,
        message: str,
        plugin_id: Optional[str] = None,
        extra_details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            error_code,
            message,
            {"plugin_id": plugin_id, **(extra_details or {})}
        )


class PluginNotLoadedError(PluginDomainException):
    def __init__(
        self,
        plugin_id: str | None = None
    ) -> None:
        super().__init__(
            "PLUGIN_NOT_LOADED",
            f"Plugin {plugin_id} is not loaded.",
            plugin_id, {}
        )


class PluginDataTypeRefInCompileTime(PluginDomainException):
    def __init__(
        self,
        datatype_fqn: str,
        plugin_id: str | None = None
    ) -> None:
        super().__init__(
            "PLUGIN_DATATYPE_REF_COMPILE_TIME",
            f"{datatype_fqn} must be PluginDatatypeSpec in compile time so a DataTypeSpec can be generated",
            plugin_id, {}
        )


class PluginMissingNodeCache(PluginDomainException):
    def __init__(
        self,
        plugin_id: str | None = None
    ) -> None:
        super().__init__(
            "PLUGIN_MISSING_NODE_CACHE",
            f"Plugin {plugin_id} doesn't have nodes_cache set up",
            plugin_id, {}
        )


class PluginMissingNodeCacheEntry(PluginDomainException):
    def __init__(
        self,
        node_fqn: str,
        plugin_id: str | None = None
    ) -> None:
        super().__init__(
            "PLUGIN_MISSING_NODE_CACHE_ENTRY",
            f"Plugin {plugin_id}'s nodes_cache is missing an entry for {node_fqn}",
            plugin_id, {"node_fqn": node_fqn}
        )

# Plugin Version

class IncompatibleVersionPluginError(PluginDomainException):
    def __init__(
        self,
        plugin_id: str,
        dependency_id: str,
        target_version: str,
        current_version: str
    ) -> None:
        super().__init__(
            "INCOMPATIBLE_DEPENDENCY_VERSION",
            f"Plugin {plugin_id} is not compatible with {dependency_id}'s version ({current_version}). Plugin requirement: {target_version}",
            plugin_id, {
                "dependency_id": dependency_id,
                "target_version": target_version, 
                "current_version": current_version
            }
        )

# Plugin Dependencies

class PluginMissingDependency(PluginDomainException):
    def __init__(
        self,
        plugin_id: str,
        loaded_plugins: list[str],
        plugin_dependencies: dict[str, str]
    ) -> None:
        missing_dependencies: list[str] = [
            dependency for dependency in plugin_dependencies
            if not dependency in loaded_plugins
        ]
        super().__init__(
            "PLUGIN_MISSING_DEPENDENCY",
            f"Plugin {plugin_id} dependencies weren't loaded. Missing dependencies: {missing_dependencies}",
            plugin_id, {"loaded_plugins": loaded_plugins, "dependencies": plugin_dependencies, "missing_dependencies": missing_dependencies}
        )

class PluginCircularDependencyError(PluginDomainException):
    def __init__(
        self,
        plugin_id: Optional[str],
        involved_plugins: list[str]
    ) -> None:
        super().__init__(
            "PLUGIN_CIRCULAR_DEPENDENCY_ERROR",
            f"Found circular dependency between plugins: {involved_plugins}",
            plugin_id, {"involved_plugins": involved_plugins}
        )

# Plugin Load Stuff

class PluginMissingSourceHash(PluginDomainException):
    def __init__(
        self,
        plugin_id: str | None = None
    ) -> None:
        super().__init__(
            "PLUGIN_MISSING_SOURCE_HASH",
            f"Plugin {plugin_id} was not hashed.",
            plugin_id
        )

class DuplicatePluginError(PluginDomainException):
    def __init__(
        self,
        plugin_id: str | None = None,
        plugin_list: Optional[list[str]] = None
    ) -> None:
        super().__init__(
            "DUPLICATE_PLUGIN_FOUND",
            f"Plugin {plugin_id} was probably loaded twice. Plugin List: {plugin_list or "not provided"}",
            plugin_id, {"plugin_list": plugin_list}
        )

# 

class MissingCacheFilesError(PluginDomainException):
     def __init__(
        self,
        plugin_id: str,
        target_file: Path,
    ) -> None:
        super().__init__(
            "MISSING_CACHE_FILES",
            f"Plugin {plugin_id} is missing {target_file.name} file. Path: {target_file}",
            plugin_id, {"target_file": target_file}
        )
