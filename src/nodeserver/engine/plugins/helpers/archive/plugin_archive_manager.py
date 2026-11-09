import logging
import re
import zipfile
from pathlib import Path

from packaging.version import InvalidVersion, Version
from pydantic import ValidationError

from nodeserver.engine.plugins.helpers.archive.plugin_unpacker import PluginUnpacker
from nodeserver.engine.plugins.protocols.plugin_archive import ARCHIVE_FORMAT_VERSION, STATE_DIR_NAME, PluginArchive
from nodeserver.engine.plugins.protocols.plugin_archive import ARCHIVE_EXTENSION, ARCHIVE_INFO_NAME
from nodeserver.engine.plugins.protocols.plugin_archive import EnginePluginArchive

logger = logging.getLogger("nds.plugins")


_PACKAGE_ID_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.\-]*$")

class PluginArchiveManager:
    @classmethod
    def read_archive(cls, path: Path) -> EnginePluginArchive:
        if not zipfile.is_zipfile(path):
            raise Exception(f"not a valid zip file (incomplete copy?). Path: {path}")

        try:
            with zipfile.ZipFile(path) as zip_file:
                info = PluginArchive.model_validate_json(zip_file.read(ARCHIVE_INFO_NAME))
        
        except ValidationError as e:
            raise Exception(f"Failed to validate info file: {e}")
        
        except (ValueError, zipfile.BadZipFile) as e:
            raise Exception(f"Unreadable {ARCHIVE_INFO_NAME}: {e}")

        if info.format_version != ARCHIVE_FORMAT_VERSION:
            raise Exception(
                f"unsupported archive format (engine reads format_version {ARCHIVE_FORMAT_VERSION})"
            )

        package_id = info.package_id
        if not isinstance(package_id, str) or not _PACKAGE_ID_RE.match(package_id):
            raise Exception(f"invalid package_id: {package_id!r}")

        try:
            version = Version(str(info.plugin_version))
        
        except InvalidVersion:
            raise Exception(f"invalid plugin_version: {info.plugin_version!r}") from None

        return EnginePluginArchive(**info.__dict__, path=path)

    @classmethod
    def sync_archives(cls, plugins_folder: Path, extraction_folder: Path) -> list[Path]:
        if not plugins_folder.is_dir():
            return []

        selected_archives: dict[str, EnginePluginArchive] = {}
        for path in sorted(plugins_folder.glob(f"*{ARCHIVE_EXTENSION}")):
            try:
                archive = cls.read_archive(path)
            
            except Exception as e:
                logger.error("Skipping plugin archive %s: %s", path.name, e)
                continue

            current = selected_archives.get(archive.package_id)
            if current is None:
                selected_archives[archive.package_id] = archive
                continue

            if archive.plugin_version > current.plugin_version:
                logger.warning("Multiple archives for %s: using %s, ignoring %s", archive.package_id, path.name, current.path.name)
                selected_archives[archive.package_id] = archive
            else:
                logger.warning("Multiple archives for %s: using %s, ignoring %s", archive.package_id, current.path.name, path.name)

        installed: list[Path] = []
        for archive in selected_archives.values():
            try:
                installed.append(PluginUnpacker.install_archive(archive, plugins_folder, extraction_folder))
            except (Exception, OSError) as e:
                logger.error("Failed to install plugin archive %s: %s", archive.path.name, e)

        cls._remove_orphans(plugins_folder, extraction_folder, set(selected_archives))
        return installed

    # -- utils

    @classmethod
    def _remove_orphans(cls, plugins_folder: Path, extracted_plugins_folder: Path, active_ids: set[str]) -> None:
        state_dir = plugins_folder / STATE_DIR_NAME
        if not state_dir.is_dir():
            return

        for state_path in state_dir.glob("*.json"):
            package_id = state_path.stem
            if package_id in active_ids:
                continue

            state = PluginUnpacker.read_archive_state(state_path)
            if state:
                archive_name = state.archive_name
                if archive_name and (plugins_folder / archive_name).exists():
                    continue

            logger.info("Archive of plugin %s was removed. Uninstalling it.", package_id)
            try:
                PluginUnpacker.remove_installed(plugins_folder, extracted_plugins_folder, package_id)
            
            except OSError as e:
                logger.error("Failed to uninstall plugin %s: %s", package_id, e)
