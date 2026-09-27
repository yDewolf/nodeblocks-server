import json
from pathlib import Path
from typing import Optional, Type

from nodeserver.engine.exceptions.plugin_exceptions import PluginNotLoadedError
from nodeserver.engine.plugins.helpers.plugin_manifest_helper import PluginManifestHelper
from nodeserver.engine.plugins.helpers.plugin_scanner import PluginScanner
from nodeserver.engine.plugins.plugin_compiler import PluginCompiler
from nodeserver.engine.plugins.protocols.plugin_datatypes import PluginDatatypeRef
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.manifest.package_manifest import ManifestPackage

class PluginManager:
    registry: TypeRegistry

    scanner: PluginScanner
    compiler: PluginCompiler

    _loaded_packages: dict[str, ManifestPackage] # package_id -> ManifestPackage
    _plugin_manifests: dict[str, PluginManifest] # package_id -> PluginManifest

    _loaded_datatypes: dict[str, PluginDatatypeRef]

    def __init__(
        self,
        registry: TypeRegistry,
        scanner: Optional[PluginScanner] = None,
        compiler: Optional[PluginCompiler] = None
    ):
        self.registry = registry
        self.scanner = scanner or PluginScanner()
        self.compiler = compiler or PluginCompiler(registry=registry)
        self.reset_packages()


    def reset_packages(self):
        self._loaded_datatypes = {}

        self._loaded_packages = {}
        self._plugin_manifests = {}


    def compile_plugins(self, source_folder: Path, save_to_disk: bool = True, output_folder: Optional[Path] = None) -> list[ManifestPackage]:
        """
        Scans a folder using PluginScanner then compiles each plugin found by it
        optionally saves ManifestPackage json (for fast boot)
        """
        source_folder = Path(source_folder)

        if save_to_disk and output_folder:
            output_folder.mkdir(parents=True, exist_ok=True)

        discovered_manifests = self.scanner.discover_plugins(source_folder)
        compiled_packages: list[ManifestPackage] = []

        for manifest, path in discovered_manifests:
            package: ManifestPackage = self.compiler.compile_manifest(manifest)
            compiled_packages.append(package)

            if save_to_disk:
                out_folder = output_folder or PluginManifestHelper.get_plugin_cache_folder(path.parent)
                if not out_folder.exists():
                    out_folder.mkdir()
                
                PluginManifestHelper.save_package_manifest(package, out_folder)
                PluginManifestHelper.save_plugin_manifest(manifest, out_folder)

            self.index_plugin(manifest)

        return compiled_packages


    def load_plugin_manifests(self, manifests_folder: Path) -> dict[str, ManifestPackage]:
        """
        Loads and registers specs from packages .manifest.json pre-compiled 
        in a folder (see compile_plugins(...))
        """
        manifests_folder = Path(manifests_folder)
        if not manifests_folder.exists():
            return {}

        for manifest_file in PluginManifestHelper.iterate_manifest_cache_files(manifests_folder):
            package = PluginManifestHelper.load_package_manifest(manifest_file)
            self.register_compiled_package(package)

        for plugin_file in PluginManifestHelper.iterate_plugin_cache_files(manifests_folder):
            plugin_manifest = PluginManifestHelper.load_plugin_manifest(plugin_file)

            # FIXME: uncomment this if needed. For now it doesn't really matter if PluginManifest.data_types is PluginDatatypeRef
            # converted_datatypes: list[PluginDatatypeSpec] = []
            # for datatype in plugin_manifest.data_types:
            #     if not isinstance(datatype, PluginDatatypeSpec):
            #         spec = self.registry.get_datatype_spec(datatype.fqn)
            #         converted_datatypes.append(PluginDatatypeSpec.from_ref_and_spec(
            #             datatype, spec
            #         ))
            
            # plugin_manifest.data_types = converted_datatypes
            self.index_plugin(plugin_manifest)

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

    # Indexing

    def index_plugin(self, plugin_manifest: PluginManifest):
        self._plugin_manifests[plugin_manifest.package_id] = plugin_manifest
        
        # TODO: index other stuff
        for datatype in plugin_manifest.data_types:
            self._loaded_datatypes[datatype.fqn] = datatype
        

    # Ensures

    def ensure_plugin_manifest(self, package_id: str) -> PluginManifest:
        if not package_id in self._plugin_manifests:
            raise PluginNotLoadedError(package_id)

        return self._plugin_manifests[package_id]

    def ensure_plugin_datatype_ref(self, datatype_fqn: str) -> PluginDatatypeRef:
        if not datatype_fqn in self._loaded_datatypes:
            raise KeyError()
        
        return self._loaded_datatypes[datatype_fqn]

    # Getters

    def get_plugin_manifest(self, package_id: str) -> Optional[PluginManifest]:
        return self._plugin_manifests.get(package_id)

    def is_plugin_loaded(self, package_id: str) -> bool:
        return package_id in self._loaded_packages

    def get_loaded_package(self, package_id: str) -> Optional[ManifestPackage]:
        return self._loaded_packages.get(package_id)

    def get_all_loaded_packages(self) -> dict[str, ManifestPackage]:
        return self._loaded_packages.copy()

    # Datatype Getters

    def get_plugin_datatype_ref(self, datatype_fqn: str) -> Optional[PluginDatatypeRef]:
        return self._loaded_datatypes.get(datatype_fqn)
