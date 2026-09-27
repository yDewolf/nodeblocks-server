
from pathlib import Path

from nodeserver.protocols.manifest.package_manifest import ManifestPackage


class PluginManifestHelper:
    @staticmethod
    def save_package_manifest(package: ManifestPackage, target_folder: Path):
        target_file = target_folder / f"{package.package_id}.manifest.json"
        with open(target_file, "w", encoding="utf-8") as file:
            file.write(package.model_dump_json(indent=2))
    
