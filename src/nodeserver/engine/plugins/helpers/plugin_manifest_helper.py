
import json
from pathlib import Path
from typing import Iterator

from nodeserver.engine.exceptions.plugin.plugin_internal_exceptions import MissingCacheFilesError
from nodeserver.engine.plugins.protocols.plugin_list_cache import PluginListCache
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.protocols.manifest.package_manifest import ManifestPackage


class PluginManifestHelper:
    PLUGIN_CACHE_FOLDERNAME = "__plugin_cache__"
    PLUGIN_LIST_CACHE_FILENAME = ".plugin_list.json"

    @staticmethod
    def make_plugin_folder_structure(target_folder: Path, plugin_id: str) -> Path:
        plugin_folder = target_folder / plugin_id
        plugin_folder.mkdir(exist_ok=True)

        return plugin_folder

    @staticmethod
    def get_plugin_cache_folder(plugin_folder: Path) -> Path:
        return plugin_folder / PluginManifestHelper.PLUGIN_CACHE_FOLDERNAME

    @staticmethod
    def ensure_cache_file(cache_folder: Path, plugin_id: str) -> Path:
        file_path = cache_folder / f"{plugin_id}.manifest.json"
        if not file_path.exists():
            raise MissingCacheFilesError(
                plugin_id, file_path
            )
        
        return file_path
        

    @staticmethod
    def iterate_plugin_cache_files(folder: Path) -> Iterator[Path]:
        return folder.rglob(f"{PluginManifestHelper.PLUGIN_CACHE_FOLDERNAME}/*.plugin.json")

    @staticmethod
    def iterate_manifest_cache_files(folder: Path) -> Iterator[Path]:
        return folder.rglob(f"{PluginManifestHelper.PLUGIN_CACHE_FOLDERNAME}/*.manifest.json")


    @staticmethod
    def save_package_manifest(package: ManifestPackage, target_folder: Path):
        target_file = target_folder / f"{package.package_id}.manifest.json"
        with open(target_file, "w", encoding="utf-8") as file:
            file.write(package.model_dump_json(indent=2))
    
    @staticmethod
    def save_plugin_manifest(plugin_manifest: PluginManifest, target_folder: Path):
        plugin_file = target_folder / f"{plugin_manifest.package_id}.plugin.json"
        with open(plugin_file, "w", encoding="utf-8") as file:
            file.write(plugin_manifest.model_dump_json(indent=2))

    @staticmethod
    def load_package_manifest(file_path: Path) -> ManifestPackage:
        with open(file_path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
            package = ManifestPackage.model_validate(raw_data)
            return package

    @staticmethod
    def load_plugin_manifest(file_path: Path) -> PluginManifest:
        with open(file_path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
            plugin_manifest = PluginManifest.model_validate(raw_data)
            return plugin_manifest


    @staticmethod
    def save_plugin_list_cache(plugins_folder: Path, cache: PluginListCache):
        file_path = plugins_folder / PluginManifestHelper.PLUGIN_LIST_CACHE_FILENAME
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(cache.model_dump_json(indent=2))
    
    @staticmethod
    def load_or_create_plugin_list_cache(plugins_folder: Path) -> PluginListCache:
        file_path = plugins_folder / PluginManifestHelper.PLUGIN_LIST_CACHE_FILENAME
        if not file_path.exists():
            data = PluginListCache(cached_plugins={})
            file_path.write_text(data.model_dump_json(indent=2), encoding="utf-8")
            return data
        
        with open(file_path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
            return PluginListCache.model_validate(raw_data)
