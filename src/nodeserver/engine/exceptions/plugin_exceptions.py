
from typing import Any, Callable, Optional, Type

from nodeserver.engine.exceptions.base_exceptions import EngineDomainError


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


class InvalidPluginDecoratorUsage(PluginDomainException):
    def __init__(
        self,
        cls: Type,
        decorator: Callable,
        plugin_id: str | None = None
    ) -> None:
        super().__init__(
            "INVALID_PLUGIN_DECORATOR_USAGE", 
            f"Invalid usage of {decorator.__name__} for class {cls}", 
            plugin_id, {"cls": cls, "decorator": decorator}
        )


class InvalidDatatypeBinding(PluginDomainException):
    def __init__(
        self,
        datatype_id: str,
        class_path: str,
        message: Optional[str] = None, 
        error_code: str = "INVALID_DATATYPE_BIND",
    ) -> None:
    
        super().__init__(
            error_code, 
            message or f"Invalid Datatype Binding for {datatype_id}", 
            extra_details={"datatype_id": datatype_id, "class_path": class_path}
        )

class MissingNamespacePluginDataType(InvalidDatatypeBinding):
    def __init__(
        self, 
        datatype_id: str,
        class_path: str,
    ) -> None:
    
        super().__init__(
            datatype_id,
            class_path,
            error_code="MISSING_NAMESPACE", 
            message=f"Missing namespace for datatype binding: {datatype_id} ({class_path})", 
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

class InvalidPluginNodeClassPath(PluginDomainException):
    def __init__(
        self,
        class_path: str,
        plugin_id: str | None = None
    ) -> None:
        super().__init__(
            "INVALID_PLUGIN_NODE_CLASS_PATH", 
            f"{class_path} is not a valid BaseNode class path in plugin {plugin_id}", 
            plugin_id, {"class_path": class_path}
        )
