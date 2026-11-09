
import hashlib
import logging
from pathlib import Path, PurePosixPath
import shutil
from typing import Optional
import zipfile

from pydantic import ValidationError

from nodeserver.engine.plugins.helpers.plugin_manifest_helper import PluginManifestHelper
from nodeserver.engine.plugins.protocols.plugin_archive import ARCHIVE_INFO_NAME, STATE_DIR_NAME, ArchiveStatuses, EnginePluginArchive, PluginArchiveState
from nodeserver.engine.utils.file_utils import rmtree

logger = logging.getLogger("nds.plugins")

MAX_ARCHIVE_FILES = 50_000
MAX_UNCOMPRESSED_BYTES = 2 * 1024**3

class PluginUnpacker:
    @classmethod
    def install_archive(cls, archive: EnginePluginArchive, plugins_folder: Path, extraction_folder: Optional[Path] = None) -> Path:
        extraction_folder = extraction_folder or plugins_folder
        
        package_id = archive.package_id
        target = extraction_folder / package_id
        state = cls.read_archive_state(cls._state_path(extraction_folder, package_id))
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
            cls.remove_installed(plugins_folder, extraction_folder, package_id)

        logger.info("Extracting plugin archive %s -> %s", archive.path.name, target)
        cls._extract(archive, plugins_folder, sha256, extraction_folder=extraction_folder)
        return target

    @classmethod
    def remove_installed(cls, plugins_folder: Path, extraction_folder: Path, package_id: str) -> None:
        installed_path = extraction_folder / package_id
        if installed_path.exists(): rmtree(installed_path)
        
        cls._state_path(extraction_folder, package_id).unlink(missing_ok=True)
        cls._forget_cached_hash(plugins_folder, package_id)

    # -- helpers

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
                cls.remove_installed(plugins_folder, extraction_folder, package_id)
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

    # -- utils

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()

        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        
        return h.hexdigest()

    @staticmethod
    def _forget_cached_hash(plugins_folder: Path, package_id: str) -> None:
        cache = PluginManifestHelper.load_or_create_plugin_list_cache(plugins_folder)
        if cache.cached_plugins.pop(package_id, None) is not None:
            PluginManifestHelper.save_plugin_list_cache(plugins_folder, cache)

    # -- state utils

    @staticmethod
    def _state_path(extraction_folder: Path, package_id: str) -> Path:
        return extraction_folder / STATE_DIR_NAME / f"{package_id}.json"

    @staticmethod
    def read_archive_state(path: Path) -> Optional[PluginArchiveState]:
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
    