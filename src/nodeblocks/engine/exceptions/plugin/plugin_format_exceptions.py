from pathlib import Path
from typing import Any, Optional

from nodeblocks.engine.exceptions.plugin.plugin_internal_exceptions import PluginDomainException


class PluginFormatException(PluginDomainException):
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

class SymlinkInPluginDir(PluginFormatException):
    def __init__(
        self,
        plugin_dir: Path,
        posix: str,
    ) -> None:
        super().__init__(
            "SYMLINKS_NOT_ALLOWED",
            f"symlinks are not allowed in plugins: {posix}",
            None,
            {"plugin_dir": plugin_dir, "posix": posix}
        )

class InvalidPluginFolder(PluginFormatException):
    def __init__(
        self,
        plugin_dir: Path,
        message: str,
        package_id: Optional[str] = None
    ) -> None:
        super().__init__(
            "INVALID_PLUGIN_FOLDER",
            message,
            package_id,
            {"plugin_dir": plugin_dir}
        )


class InvalidPluginFile(PluginFormatException):
    def __init__(
        self,
        plugin_file: Path,
        message: Optional[str] = None,
        error_code: str = "INVALID_PLUGIN_FILE", 
        extra: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            error_code,
            message or f"Invalid plugin.py file: {plugin_file}",
            None,
            {"plugin_file": plugin_file, **(extra or {})}
        )

class MissingPluginClassInFile(InvalidPluginFile):
    def __init__(
        self,
        plugin_file: Path,
    ) -> None:
        super().__init__(
            plugin_file,
            f"Couldn't find a Plugin class in {plugin_file}",
            error_code="MISSING_PLUGIN_CLASS"
        )

