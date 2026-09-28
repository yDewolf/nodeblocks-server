from collections import deque
from typing import Optional
from packaging.version import Version, parse as parse_version
from packaging.specifiers import SpecifierSet

from nodeserver.engine.engine_version import CURRENT_ENGINE_VERSION
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest


class PluginVersionManager:
    engine_version: Version
    
    def __init__(self, current_engine_version: str = CURRENT_ENGINE_VERSION):
        self.engine_version = parse_version(current_engine_version)

    def validate_engine_compatibility(self, min_engine_version: Optional[str], package_id: str) -> None:
        if not min_engine_version:
            return

        spec_str = min_engine_version if any(op in min_engine_version for op in "<>=!") else f">={min_engine_version}"
        specifier = SpecifierSet(spec_str)

        if not self.engine_version in specifier:
            raise Exception("Dependency error wrong engine version")

    def validate_plugin_dependencies(self, target_manifest: PluginManifest, installed_plugins: dict[str, PluginManifest]) -> None:
        for dep_package_id, version_req in target_manifest.dependencies.items():
            if not dep_package_id in installed_plugins:
                raise Exception("Dependency error not installed")

            installed_manifest = installed_plugins[dep_package_id]
            installed_version = parse_version(installed_manifest.version)

            spec_str = version_req if any(op in version_req for op in "<>=!") else f">={version_req}"
            specifier = SpecifierSet(spec_str)

            if installed_version not in specifier:
                raise Exception("Dependency error wrong version")
