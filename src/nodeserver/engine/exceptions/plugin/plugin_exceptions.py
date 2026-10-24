
from typing import Callable, Optional, Type

from nodeserver.engine.exceptions.plugin.plugin_internal_exceptions import PluginDomainException

# Exceptions that are probably caused by the Plugin's Developer

# Pre PluginCompiler compile

class InvalidPluginDecoratorUsage(PluginDomainException):
    def __init__(
        self,
        cls: Type,
        message: str,
        decorator: Callable,
        plugin_id: str | None = None
    ) -> None:
        super().__init__(
            "INVALID_PLUGIN_DECORATOR_USAGE", 
            f"Invalid usage of {decorator.__name__} for class {cls}: {message}", 
            plugin_id, {"cls": cls, "decorator": decorator}
        )

class InvalidNodeDecoratedClass(InvalidPluginDecoratorUsage):
    def __init__(
        self,
        cls: Type,
        decorator: Callable,
        plugin_id: str | None = None
    ) -> None:
        super().__init__(
            cls,
            f"{decorator.__name__} must be used on a BaseNode class.",
            decorator,
            plugin_id
        )


class InvalidDatatypeDecoratedClass(InvalidPluginDecoratorUsage):
    def __init__(
        self,
        cls: Type,
        decorator: Callable,
        plugin_id: str | None = None
    ) -> None:
        super().__init__(
            cls,
            f"{decorator.__name__} must be used on a PluginDataType class.",
            decorator,
            plugin_id
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

# General errors

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

# Version stuff

class IncompatibleEngineVersionPluginError(PluginDomainException):
    def __init__(
        self,
        plugin_id: str,
        target_engine_version: str,
        current_engine_version: str
    ) -> None:
        super().__init__(
            "INCOMPATIBLE_PLUGIN_ERROR",
            f"Plugin {plugin_id} is not compatible with current engine version ({current_engine_version}). Plugin requirement: {target_engine_version}",
            plugin_id, {
                "target_engine_version": target_engine_version,
                "current_engine_version": current_engine_version
            }
        )
class IncompatibleApiVersionPluginError(PluginDomainException):
    def __init__(
        self,
        plugin_id: str,
        target_api_version: str,
        current_api_version: str
    ) -> None:
        super().__init__(
            "INCOMPATIBLE_PLUGIN_ERROR",
            f"Plugin {plugin_id} is not compatible with current plugin api version ({current_api_version}). Plugin requirement: {target_api_version}",
            plugin_id, {
                "target_api_version": target_api_version,
                "current_api_version": current_api_version
            }
        )
