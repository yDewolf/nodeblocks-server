
from typing import Any, Optional

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
