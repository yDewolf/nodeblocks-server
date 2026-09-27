
import json
from pathlib import Path

from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.protocols.manifest.package_manifest import ManifestPackage


class PluginManifestHelper:
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
