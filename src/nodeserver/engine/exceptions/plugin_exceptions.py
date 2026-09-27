
from typing import Any, Optional

from nodeserver.engine.exceptions.base_exceptions import EngineDomainError


class PluginDomainException(EngineDomainError):
    pass


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
            {"datatype_id": datatype_id, "class_path": class_path}
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
