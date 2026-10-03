from collections import deque
import logging
from pathlib import Path
from typing import Optional, Type

from nodeserver.engine.engine_version import CURRENT_ENGINE_VERSION
from nodeserver.engine.exceptions.plugin.plugin_internal_exceptions import DuplicatePluginError, PluginCircularDependencyError, PluginMissingDependency, PluginNotLoadedError
from nodeserver.engine.plugins.helpers.plugin_manifest_helper import PluginManifestHelper
from nodeserver.engine.plugins.helpers.plugin_scanner import PluginScanner
from nodeserver.engine.plugins.helpers.plugin_version_manager import PluginVersionManager
from nodeserver.engine.plugins.protocols.plugin_specs import PluginDatatypeRef
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.engine.registry.type_registry import TypeSpecRegistry
from nodeserver.protocols.manifest.package_manifest import ManifestPackage

logger = logging.getLogger("nds.plugins")

class PluginSpecManager:
    registry: TypeSpecRegistry
    scanner: PluginScanner
    version_manager: PluginVersionManager

    _loaded_packages: dict[str, ManifestPackage] # package_id -> ManifestPackage
    _installed_plugins: dict[str, PluginManifest] # package_id -> PluginManifest
    _loaded_datatypes: dict[str, PluginDatatypeRef]

    def __init__(
        self,
        registry: TypeSpecRegistry,
        scanner: Optional[PluginScanner] = None,
        plugin_version_manager: Optional[PluginVersionManager] = None
    ):
        self.version_manager = plugin_version_manager or PluginVersionManager(CURRENT_ENGINE_VERSION)
        
        self.registry = registry
        self.scanner = scanner or PluginScanner()
        self.reset_packages()


    def reset_packages(self):
        if hasattr(self, "_loaded_packages"):
            logger.warning(
                "Resetting plugin spec manager loaded packages. Loaded packages: %s", 
                ", ".join([package_id for package_id in self._loaded_packages])
            )
        
        self._loaded_datatypes = {}
        self._loaded_packages = {}
        self._installed_plugins = {}
    
    def load_plugin_manifests(self, manifests_folder: Path) -> dict[str, ManifestPackage]:
        """
        Loads and registers specs from packages .manifest.json pre-compiled 
        in a folder (see compile_plugins(...))
        """
        manifests_folder = Path(manifests_folder)
        logger.info("Loading plugin manifests from: %s...", manifests_folder)
        if not manifests_folder.exists():
            logger.error("Failed to load plugins since the provided folder doesn't exist.")
            return {}

        plugin_manifests: list[tuple[PluginManifest, Path]] = [
            (PluginManifestHelper.load_plugin_manifest(cache_file), cache_file) 
            for cache_file in PluginManifestHelper.iterate_plugin_cache_files(manifests_folder)
        ]

        logger.info(
            "Found %s plugins: %s", 
            len(plugin_manifests), 
            ", ".join([manifest.package_id for manifest, _ in plugin_manifests])
        )
        for plugin_manifest, cache_file in self.resolve_plugin_load_order(plugin_manifests):
            self.version_manager.validate_plugin_requirements(
                plugin_manifest, self._installed_plugins
            )
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

        for manifest_file in PluginManifestHelper.iterate_manifest_cache_files(manifests_folder):
            package = PluginManifestHelper.load_package_manifest(manifest_file)
            if self.is_plugin_loaded(package.package_id):
                self.register_compiled_package(package)

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

    
    def _load_plugin_from_cache(self, manifest: PluginManifest, plugin_file_path: Path) -> ManifestPackage:
        cache_folder = PluginManifestHelper.get_plugin_cache_folder(plugin_file_path.parent)
        manifest_file = PluginManifestHelper.ensure_cache_file(cache_folder, manifest.package_id)
        package = PluginManifestHelper.load_package_manifest(manifest_file)
        self.register_compiled_package(package)
        self.index_plugin(manifest)

        return package


    # Indexing

    def index_plugin(self, plugin_manifest: PluginManifest):
        logger.debug("Indexing plugin - package_id: %s", plugin_manifest.package_id)
        self._installed_plugins[plugin_manifest.package_id] = plugin_manifest
        
        # TODO: index other stuff
        for datatype in plugin_manifest.data_types:
            self._loaded_datatypes[datatype.fqn] = datatype

    # Ensures

    def ensure_package(self, package_id: str) -> ManifestPackage:
        if not package_id in self._loaded_packages:
            raise KeyError(f"Package {package_id} is not loaded") # TODO: exception

        return self._loaded_packages[package_id]

    def ensure_plugin_manifest(self, package_id: str) -> PluginManifest:
        if not package_id in self._installed_plugins:
            raise PluginNotLoadedError(package_id)

        return self._installed_plugins[package_id]

    def ensure_plugin_datatype_ref(self, datatype_fqn: str) -> PluginDatatypeRef:
        if not datatype_fqn in self._loaded_datatypes:
            raise KeyError()
        
        return self._loaded_datatypes[datatype_fqn]

    # Getters

    def get_plugin_manifest(self, package_id: str) -> Optional[PluginManifest]:
        return self._installed_plugins.get(package_id)

    def is_package_loaded(self, package_id: str) -> bool:
        return package_id in self._loaded_packages

    def is_plugin_loaded(self, package_id: str) -> bool:
        return package_id in self._installed_plugins

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
                raise DuplicatePluginError(
                    manifest.package_id, 
                    [plugin_manifest.package_id for plugin_manifest, _ in manifests]    
                )
            
            plugins_map[manifest.package_id] = (manifest, path)

        in_degree: dict[str, int] = {pkg_id: 0 for pkg_id in plugins_map}
        graph: dict[str, list[str]] = {pkg_id: [] for pkg_id in plugins_map}

        for pkg_id, (manifest, path) in plugins_map.items():
            for dep_id in manifest.dependencies.keys():
                if dep_id not in plugins_map:
                    raise PluginMissingDependency(
                        manifest.package_id,
                        [plugin_manifest.package_id for plugin_manifest, _ in manifests],
                        manifest.dependencies
                    )
                
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
            raise PluginCircularDependencyError(
                plugin_id=None,
                involved_plugins=unresolved
            )

        return ordered_manifests
