from typing import Any

from nodeserver.engine.exceptions.base_exceptions import EngineDomainError


class SpecBuildDomainError(EngineDomainError):
    pass

class AnnotationDataTypeInferError(SpecBuildDomainError):
    def __init__(
        self, 
        annotation: Any,
        message: str, 
    ) -> None:
        super().__init__(
            "INVALID_DATATYPE_ANNOTATION", 
            f"Invalid Datatype Annotation: {message}", 
            {"annotation": annotation}
        )

