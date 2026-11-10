
from pathlib import Path
from typing import Any, Optional

from nodeblocks.engine.exceptions.plugin.plugin_internal_exceptions import PluginDomainException


class PluginArchiveException(PluginDomainException):
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


class FailedArchiveInstall(PluginArchiveException):
    def __init__(
        self,
        message: str,
        target: Path,
        archive_path: Path,
        plugin_id: Optional[str] = None,
        solution: str = "Not Provided"
    ) -> None:
        super().__init__(
            "FAILED_ARCHIVE_INSTALL",
            message + f" \nSolution: {solution}",
            plugin_id,
            {"target": target, "archive_path": archive_path}
        )

class InvalidPluginMemberFile(PluginArchiveException):
    def __init__(
        self,
        message: str,
        member_name: str,
        plugin_id: Optional[str] = None
    ) -> None:
        super().__init__(
            "INVALID_PLUGIN_MEMBER",
            message,
            plugin_id,
            {"member_name": member_name}
        )


class TooManyFilesInArchive(PluginArchiveException):
    def __init__(
        self,
        members: int,
        max_members: int,
        plugin_id: Optional[str] = None
    ) -> None:
        super().__init__(
            "TOO_MANY_FILES_IN_ARCHIVE",
            f"too many files in plugin archive ({members} > {max_members})",
            plugin_id,
            {"members": members, "max_members": max_members}
        )

class ArchiveIsTooBig(PluginArchiveException):
    def __init__(
        self,
        total_bytes: int,
        max_bytes: int,
        plugin_id: Optional[str] = None
    ) -> None:
        super().__init__(
            "PLUGIN_ARCHIVE_IS_TOO_BIG",
            f"archive is too large when extracted ({total_bytes} > {max_bytes} bytes)",
            plugin_id,
            {"total_bytes": total_bytes, "max_bytes": max_bytes}
        )


class InvalidArchiveZip(PluginArchiveException):
    def __init__(
        self,
        path: Path,
        message: str,
        plugin_id: Optional[str] = None
    ) -> None:
        super().__init__(
            "INVALID_ARCHIVE_ZIP",
            message,
            plugin_id,
            {"path": path}
        )

class InvalidArchiveInfoFile(PluginArchiveException):
    def __init__(
        self,
        path: Path,
        message: str,
        plugin_id: Optional[str] = None
    ) -> None:
        super().__init__(
            "INVALID_ARCHIVE_INFO_FILE",
            message,
            plugin_id,
            {"path": path}
        )


class UnsupportedArchiveFormat(PluginArchiveException):
    def __init__(
        self,
        format: int,
        supported_format: int,
        plugin_id: Optional[str] = None
    ) -> None:
        super().__init__(
            "UNSUPPORTED_ARCHIVE_FORMAT",
            f"unsupported archive format: {format} (engine reads format_version {supported_format})",
            plugin_id,
            {"format": format, "supported_format": supported_format}
        )
