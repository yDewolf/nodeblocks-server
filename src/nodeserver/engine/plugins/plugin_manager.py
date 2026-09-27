import json
from pathlib import Path
from typing import Optional, Type

from nodeserver.engine.exceptions.plugin_exceptions import PluginNotLoadedError
from nodeserver.engine.plugins.helpers.plugin_manifest_helper import PluginManifestHelper
from nodeserver.engine.plugins.helpers.plugin_scanner import PluginScanner
from nodeserver.engine.plugins.plugin_compiler import PluginCompiler
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.manifest.package_manifest import ManifestPackage

class PluginManager:
    registry: TypeRegistry

    scanner: PluginScanner
    compiler: PluginCompiler

    _loaded_packages: dict[str, ManifestPackage] # package_id -> ManifestPackage
    _plugin_manifests: dict[str, PluginManifest] # package_id -> PluginManifest


    def __init__(
        self,
        registry: TypeRegistry,
        scanner: Optional[PluginScanner] = None,
        compiler: Optional[PluginCompiler] = None
    ):
        self.registry = registry
        self.scanner = scanner or PluginScanner()
        self.compiler = compiler or PluginCompiler(registry=registry)

        self._loaded_packages = {}
        self._plugin_manifests = {}


    def compile_plugins(self, source_folder: Path, output_folder: Path, save_to_disk: bool = True) -> list[ManifestPackage]:
        """
        Scans a folder using PluginScanner then compiles each plugin found by it
        optionally saves ManifestPackage json (for fast boot)
        """
        source_folder = Path(source_folder)
        output_folder = Path(output_folder)

        if save_to_disk:
            output_folder.mkdir(parents=True, exist_ok=True)

        discovered_manifests: list[PluginManifest] = self.scanner.discover_plugins(source_folder)
        compiled_packages: list[ManifestPackage] = []

        for manifest in discovered_manifests:
            self._plugin_manifests[manifest.package_id] = manifest

            package: ManifestPackage = self.compiler.compile_manifest(manifest)
            compiled_packages.append(package)

            if save_to_disk:
                PluginManifestHelper.save_package_manifest(package, output_folder)
                PluginManifestHelper.save_plugin_manifest(manifest, output_folder)

        return compiled_packages


    def load_plugin_manifests(self, manifests_folder: Path) -> dict[str, ManifestPackage]:
        """
        Loads and registers specs from packages .manifest.json pre-compiled 
        in a folder (see compile_plugins(...))
        """
        manifests_folder = Path(manifests_folder)
        if not manifests_folder.exists():
            return {}

        for plugin_file in manifests_folder.glob("*.plugin.json"):
            plugin_manifest = PluginManifestHelper.load_plugin_manifest(plugin_file)
            self._plugin_manifests[plugin_manifest.package_id] = plugin_manifest

        for manifest_file in manifests_folder.glob("*.manifest.json"):
            package = PluginManifestHelper.load_package_manifest(manifest_file)
            self.register_compiled_package(package)

        return self._loaded_packages

    def register_compiled_package(self, package: ManifestPackage) -> None:
        """
        Registers a ManifestPackage's types in the registry (TypeRegistry).
        Doesn't assign types to python types
        """
        for datatype_spec in package.data_types.values():
            self.registry.register_data_type(datatype_spec)

        for node_spec in package.node_types.values():
            self.registry.register_node_type(node_spec)

        self._loaded_packages[package.package_id] = package


    def ensure_plugin_manifest(self, package_id: str) -> PluginManifest:
        if not package_id in self._plugin_manifests:
            raise PluginNotLoadedError(package_id)

        return self._plugin_manifests[package_id]

    def get_plugin_manifest(self, package_id: str) -> Optional[PluginManifest]:
        return self._plugin_manifests.get(package_id)

    def is_plugin_loaded(self, package_id: str) -> bool:
        return package_id in self._loaded_packages

    def get_loaded_package(self, package_id: str) -> Optional[ManifestPackage]:
        return self._loaded_packages.get(package_id)

    def get_all_loaded_packages(self) -> dict[str, ManifestPackage]:
        return self._loaded_packages.copy()
