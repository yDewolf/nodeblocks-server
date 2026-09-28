import hashlib
from pathlib import Path

from nodeserver.engine.plugins.helpers.plugin_manifest_helper import PluginManifestHelper


class PluginHasher:
    IGNORED_PATHS = {
        PluginManifestHelper.PLUGIN_CACHE_FOLDERNAME,
        "__pycache__",
        ".git",
        ".vscode",
        ".pytest_cache"
    }

    @classmethod
    def calculate_plugin_hash(cls, plugin_dir: Path) -> str:
        hasher = hashlib.sha256()

        for file_path in sorted(plugin_dir.rglob("*")):
            if any(part in cls.IGNORED_PATHS for part in file_path.parts):
                continue

            if not file_path.is_file():
                continue
            
            rel_path = file_path.relative_to(plugin_dir).as_posix()
            hasher.update(rel_path.encode("utf-8"))

            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)

        return hasher.hexdigest()
