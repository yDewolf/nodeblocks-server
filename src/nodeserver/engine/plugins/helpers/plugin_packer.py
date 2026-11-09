import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any

from nodeserver.engine.plugins.helpers.plugin_hasher import PluginHasher
from nodeserver.engine.plugins.protocols.plugin_archive import ARCHIVE_EXTENSION, PluginArchive
from nodeserver.engine.plugins.protocols.plugin_archive import ARCHIVE_INFO_NAME

_ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)

class PluginPacker:
    EXCLUDED_PARTS = frozenset(PluginHasher.IGNORED_PATHS)
    EXCLUDED_SUFFIXES = (".pyc", ".pyo", ARCHIVE_EXTENSION)

    @classmethod
    def collect_files(cls, plugin_dir: Path) -> list[Path]:
        files: list[Path] = []
        for path in plugin_dir.rglob("*"):
            rel = path.relative_to(plugin_dir)
            if any(part in cls.EXCLUDED_PARTS for part in rel.parts):
                continue

            if path.suffix in cls.EXCLUDED_SUFFIXES:
                continue
            
            if path.is_symlink():
                # FIXME: better exceptions
                raise Exception(f"symlinks are not allowed in plugins: {rel.as_posix()}")
            
            if path.is_file():
                files.append(path)

        return sorted(files, key=lambda part: part.relative_to(plugin_dir).as_posix())

    @classmethod
    def pack(cls, plugin_dir: Path, info: PluginArchive, output_dir: Path) -> tuple[Path, int]:
        """
        Generates -> `{output_dir}/{package_id}-{version}.nbplugin`
        Returns -> archive_path, file_amount
        """

        files = cls.collect_files(plugin_dir)
        if not any(file.relative_to(plugin_dir).as_posix() == "plugin.py" for file in files):
            # FIXME: better exceptions
            raise Exception("plugin.py must be directly inside the plugin folder")

        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"{info.package_id}-{info.plugin_version}{ARCHIVE_EXTENSION}"
        tmp_path = out_path.with_name(out_path.name + ".tmp")

        try:
            with zipfile.ZipFile(tmp_path, "w") as zip_file:
                info_bytes = info.model_dump_json(indent=2).encode("utf-8")
                with zip_file.open(cls._zipinfo(ARCHIVE_INFO_NAME), "w") as dest:
                    dest.write(info_bytes)

                for file_path in files:
                    arcname = f"{info.package_id}/{file_path.relative_to(plugin_dir).as_posix()}"
                    zinfo = cls._zipinfo(arcname)
                    zinfo.file_size = file_path.stat().st_size

                    with zip_file.open(zinfo, "w") as dest, open(file_path, "rb") as src:
                        shutil.copyfileobj(src, dest)

            os.replace(tmp_path, out_path)
        
        finally:
            tmp_path.unlink(missing_ok=True)

        return out_path, len(files)

    # -- utils

    @staticmethod
    def _zipinfo(arcname: str) -> zipfile.ZipInfo:
        zinfo = zipfile.ZipInfo(arcname, date_time=_ZIP_EPOCH)
        zinfo.compress_type = zipfile.ZIP_DEFLATED

        # FIXME: this might need to be changed so Linux and Windows differ
        zinfo.create_system = 3

        zinfo.external_attr = 0o644 << 16
        return zinfo
