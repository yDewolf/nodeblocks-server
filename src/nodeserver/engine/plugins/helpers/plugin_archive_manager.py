import hashlib
import logging
import os
import re
import shutil
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Optional

from packaging.version import InvalidVersion, Version
from pydantic import ValidationError

from nodeserver.engine.plugins.helpers.plugin_manifest_helper import PluginManifestHelper
from nodeserver.engine.plugins.protocols.plugin_archive import ARCHIVE_FORMAT_VERSION, STATE_DIR_NAME, ArchiveStatuses, PluginArchive, PluginArchiveState
from nodeserver.engine.plugins.protocols.plugin_archive import ARCHIVE_EXTENSION, ARCHIVE_INFO_NAME

logger = logging.getLogger("nds.plugins")

MAX_ARCHIVE_FILES = 50_000
MAX_UNCOMPRESSED_BYTES = 2 * 1024**3

_PACKAGE_ID_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.\-]*$")


class EnginePluginArchive(PluginArchive):
    path: Path


def _rmtree(path: Path) -> None:
    def _make_writable_and_retry(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_make_writable_and_retry)
    else:
        shutil.rmtree(path, onerror=_make_writable_and_retry)


# TODO: refactor ts
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
                installed.append(cls._install_archive(archive, plugins_folder, extraction_folder))
            except (Exception, OSError) as e:
                logger.error("Failed to install plugin archive %s: %s", archive.path.name, e)

        cls._remove_orphans(plugins_folder, extraction_folder, set(selected_archives))
        return installed

    # -- utils

    @classmethod
    def _install_archive(cls, archive: EnginePluginArchive, plugins_folder: Path, extraction_folder: Optional[Path] = None) -> Path:
        extraction_folder = extraction_folder or plugins_folder
        
        package_id = archive.package_id
        target = extraction_folder / package_id
        state = cls._read_state(cls._state_path(extraction_folder, package_id))
        sha256 = cls._sha256(archive.path)

        if target.exists():
            if state is None:
                raise Exception(
                    f"Folder '{target}' already exists and was not created from an archive. "
                    "Remove the folder or the archive."
                )
            
            if state.status == ArchiveStatuses.COMPLETE and state.archive_sha256 == sha256:
                return target

            logger.info("Plugin archive changed, reinstalling %s %s", package_id, archive.plugin_version)
            cls._remove_installed(plugins_folder, extraction_folder, package_id)

        logger.info("Extracting plugin archive %s -> %s", archive.path.name, target)
        cls._extract(archive, plugins_folder, sha256, extraction_folder=extraction_folder)
        return target

    @classmethod
    def _extract(cls, archive: EnginePluginArchive, plugins_folder: Path, sha256: str, extraction_folder: Optional[Path] = None) -> None:
        extraction_folder = extraction_folder or plugins_folder

        package_id = archive.package_id
        target = extraction_folder / package_id
        state_path = cls._state_path(extraction_folder, package_id)
        
        state: PluginArchiveState = PluginArchiveState(
            package_id=package_id, plugin_version=archive.plugin_version,
            archive_name=archive.path.name, archive_sha256=sha256,
            status=ArchiveStatuses.EXTRACTING
        )

        with zipfile.ZipFile(archive.path) as zip_file:
            members = [info for info in zip_file.infolist() if info.filename != ARCHIVE_INFO_NAME]
            cls._validate_members(members, package_id, extraction_folder)
            cls._forget_cached_hash(plugins_folder, package_id)

            cls._write_state(state_path, state)
            try:
                for info in members:
                    dest = extraction_folder / info.filename
                    if info.is_dir():
                        dest.mkdir(parents=True, exist_ok=True)
                        continue
                    
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zip_file.open(info) as src, open(dest, "wb") as out:
                        shutil.copyfileobj(src, out)

                if not (target / "plugin.py").is_file():
                    raise Exception("plugin.py must be directly inside 'package_id/' in the archive")
            
            except BaseException:
                cls._remove_installed(plugins_folder, extraction_folder, package_id)
                raise

        state.status = ArchiveStatuses.COMPLETE
        cls._write_state(state_path, state)

    @staticmethod
    def _validate_members(members: list[zipfile.ZipInfo], package_id: str, extraction_folder: Path) -> None:
        if len(members) > MAX_ARCHIVE_FILES:
            raise Exception(f"too many files in plugin archive ({len(members)} > {MAX_ARCHIVE_FILES})")

        prefix = f"{package_id}/"
        root = (extraction_folder / package_id).resolve()
        total = 0
        for info in members:
            name = info.filename
            posix = PurePosixPath(name)
            if (
                not name.startswith(prefix)
                or posix.is_absolute()
                or ".." in posix.parts
                or "\\" in name
                or ":" in name
            ):
                raise Exception(f"unsafe entry in archive: {name!r}")

            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise Exception(f"symlinks are not allowed in archives: {name!r}")

            if not (extraction_folder / name).resolve().is_relative_to(root):
                raise Exception(f"entry escapes the plugin folder: {name!r}")

            total += info.file_size

        if total > MAX_UNCOMPRESSED_BYTES:
            raise Exception(
                f"archive is too large when extracted ({total} > {MAX_UNCOMPRESSED_BYTES} bytes)"
            )

    @classmethod
    def _remove_orphans(cls, plugins_folder: Path, extracted_plugins_folder: Path, active_ids: set[str]) -> None:
        state_dir = plugins_folder / STATE_DIR_NAME
        if not state_dir.is_dir():
            return

        for state_path in state_dir.glob("*.json"):
            package_id = state_path.stem
            if package_id in active_ids:
                continue

            state = cls._read_state(state_path)
            if state:
                archive_name = state.archive_name
                if archive_name and (plugins_folder / archive_name).exists():
                    continue

            logger.info("Archive of plugin %s was removed. Uninstalling it.", package_id)
            try:
                cls._remove_installed(plugins_folder, extracted_plugins_folder, package_id)
            
            except OSError as e:
                logger.error("Failed to uninstall plugin %s: %s", package_id, e)


    @classmethod
    def _remove_installed(cls, plugins_folder: Path, extraction_folder: Path, package_id: str) -> None:
        installed_path = extraction_folder / package_id
        if installed_path.exists(): _rmtree(installed_path)
        
        cls._state_path(extraction_folder, package_id).unlink(missing_ok=True)
        cls._forget_cached_hash(plugins_folder, package_id)


    # -- helpers

    @staticmethod
    def _forget_cached_hash(plugins_folder: Path, package_id: str) -> None:
        cache = PluginManifestHelper.load_or_create_plugin_list_cache(plugins_folder)
        if cache.cached_plugins.pop(package_id, None) is not None:
            PluginManifestHelper.save_plugin_list_cache(plugins_folder, cache)

    @staticmethod
    def _state_path(extraction_folder: Path, package_id: str) -> Path:
        return extraction_folder / STATE_DIR_NAME / f"{package_id}.json"

    @staticmethod
    def _read_state(path: Path) -> Optional[PluginArchiveState]:
        try:
            data = PluginArchiveState.model_validate_json(path.read_text(encoding="utf-8"))

        except ValidationError as e:
            logger.error("Failed to load plugin archive state (%s): %s", path, str(e))
            return None
        
        except (OSError, ValueError):
            return None

        return data

    @staticmethod
    def _write_state(path: Path, state: PluginArchiveState) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(state.model_dump_json(indent=2), encoding="utf-8")

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()

        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        
        return h.hexdigest()
