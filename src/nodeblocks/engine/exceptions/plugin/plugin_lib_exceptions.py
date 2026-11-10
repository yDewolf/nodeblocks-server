from typing import Any, Optional

from nodeblocks.engine.exceptions.plugin.plugin_internal_exceptions import PluginDomainException

class PluginLibDomainException(PluginDomainException):
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
            plugin_id,
            extra_details
        )

class NotAllowedToInstallLibsError(PluginLibDomainException):
    def __init__(
        self, 
        lib_fingerprint: str, 
    ) -> None:
        super().__init__(
            "NOT_ALLOWED_TO_INSTALL_LIBS", 
            f"Plugin libs {lib_fingerprint} aren't installed and current process isn't allowed to install them.", 
            plugin_id=None, 
            extra_details={}
        )

class LibCompileFailed(PluginLibDomainException):
    def __init__(
        self, 
        stderror: str,
        libs: list[str]
    ) -> None:
        super().__init__(
            "FAILED_TO_COMPILE_LIBS", 
            f"Failed to compile libs: {stderror}. Related libs: {libs}", 
            plugin_id=None, 
            extra_details={"libs": libs}
        )

