from collections import deque
import json
from pathlib import Path
from typing import Optional, Type

from nodeserver.engine.engine_version import CURRENT_ENGINE_VERSION
from nodeserver.engine.exceptions.plugin_exceptions import PluginNotLoadedError
from nodeserver.engine.plugins.helpers.plugin_manifest_helper import PluginManifestHelper
from nodeserver.engine.plugins.helpers.plugin_scanner import PluginScanner
from nodeserver.engine.plugins.helpers.plugin_version_manager import PluginVersionManager
from nodeserver.engine.plugins.plugin_compiler import PluginCompiler
from nodeserver.engine.plugins.protocols.plugin_specs import PluginDatatypeRef
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.manifest.package_manifest import ManifestPackage

class PluginManager:
    registry: TypeRegistry

    scanner: PluginScanner
    compiler: PluginCompiler
    version_manager: PluginVersionManager

    _loaded_packages: dict[str, ManifestPackage] # package_id -> ManifestPackage
    _plugin_manifests: dict[str, PluginManifest] # package_id -> PluginManifest

    _loaded_datatypes: dict[str, PluginDatatypeRef]

    def __init__(
        self,
        registry: TypeRegistry,
        scanner: Optional[PluginScanner] = None,
        compiler: Optional[PluginCompiler] = None,
        plugin_version_manager: Optional[PluginVersionManager] = None
    ):
        self.version_manager = plugin_version_manager or PluginVersionManager(CURRENT_ENGINE_VERSION)
        
        self.registry = registry
        self.scanner = scanner or PluginScanner()
        self.compiler = compiler or PluginCompiler(registry=registry)
        self.reset_packages()


    def reset_packages(self):
        self._loaded_datatypes = {}

        self._loaded_packages = {}
        self._plugin_manifests = {}

    
    def load_or_compile_plugins(self, source_folder: Path, save_to_disk: bool = True):
        """
        Scans a folder using PluginScanner then checks plugin hashes to determine
        if plugins need to be compiled or they can just be loaded
        """
        source_folder = Path(source_folder)
        cached_plugin_list = PluginManifestHelper.load_or_create_plugin_list_cache(source_folder)

        discovered_manifests = self.scanner.discover_plugins(source_folder)
        compiled_packages: list[ManifestPackage] = []
        
        for manifest, file_path in self.resolve_plugin_load_order(discovered_manifests):
            if not manifest.source_hash:
                raise Exception("didn't hash properly") # FIXME: exception

            cached_hash = cached_plugin_list.cached_plugins.get(manifest.package_id)
            if not cached_hash or cached_hash != manifest.source_hash:
                self._compile_plugin_manifest(manifest, file_path, save_to_disk)
            else:
                # TODO: improve this loading logic
                cache_folder = PluginManifestHelper.get_plugin_cache_folder(file_path.parent)
                manifest_file = PluginManifestHelper.get_manifest_cache_file(cache_folder)
                package = PluginManifestHelper.load_package_manifest(manifest_file)
                self.register_compiled_package(package)
            
            cached_plugin_list.cached_plugins[manifest.package_id] = manifest.source_hash               
            self.index_plugin(manifest)

        PluginManifestHelper.save_plugin_list_cache(source_folder, cached_plugin_list)
        return compiled_packages

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

        for manifest, file_path in self.resolve_plugin_load_order(discovered_manifests):
            package = self._compile_plugin_manifest(manifest, file_path, save_to_disk, output_folder)
            compiled_packages.append(package)
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

        plugin_manifests: list[tuple[PluginManifest, Path]] = [
            (PluginManifestHelper.load_plugin_manifest(cache_file), cache_file) 
            for cache_file in PluginManifestHelper.iterate_plugin_cache_files(manifests_folder)
        ] 
        for plugin_manifest, cache_file in self.resolve_plugin_load_order(plugin_manifests):
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

    # Single Plugin 'Actions'

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

    
    def _compile_plugin_manifest(self, manifest: PluginManifest, file_path: Path, save_to_disk: bool = True, cache_out_folder: Optional[Path] = None) -> ManifestPackage:
        modules = self.scanner.discover_modules(file_path.parent)
        self.compiler.compile_plugin_modules(manifest, modules)
        
        package: ManifestPackage = self.compiler.compile_manifest(manifest)

        if save_to_disk:
            out_folder = cache_out_folder or PluginManifestHelper.get_plugin_cache_folder(file_path.parent)
            if not out_folder.exists():
                out_folder.mkdir()
            
            PluginManifestHelper.save_package_manifest(package, out_folder)
            PluginManifestHelper.save_plugin_manifest(manifest, out_folder)

        return package



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


    # TODO: make a generalized kahn algorithm
    def resolve_plugin_load_order(self, manifests: list[tuple[PluginManifest, Path]]) -> list[tuple[PluginManifest, Path]]:
        plugins_map: dict[str, tuple[PluginManifest, Path]] = {}
        for manifest, path in manifests:
            if manifest.package_id in plugins_map:
                raise Exception("Duplicate plugin found in list")
            
            plugins_map[manifest.package_id] = (manifest, path)

        in_degree: dict[str, int] = {pkg_id: 0 for pkg_id in plugins_map}
        graph: dict[str, list[str]] = {pkg_id: [] for pkg_id in plugins_map}

        for pkg_id, (manifest, path) in plugins_map.items():
            for dep_id in manifest.dependencies.keys():
                if dep_id not in plugins_map:
                    raise Exception("Missing plugin dependency")
                
                graph[dep_id].append(pkg_id)
                in_degree[pkg_id] += 1

        queue = deque([pkg_id for pkg_id, degree in in_degree.items() if degree == 0])
        ordered_manifests: list[tuple[PluginManifest, Path]] = []

        while queue:
            current_id = queue.popleft()
            ordered_manifests.append(plugins_map[current_id])

            for dependent_id in graph[current_id]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

        if len(ordered_manifests) < len(plugins_map):
            unresolved = [pkg_id for pkg_id, degree in in_degree.items() if degree > 0]
            raise Exception(f"Circular dependency between plugins: {unresolved}")

        return ordered_manifests