import logging
from pathlib import Path
from typing import Optional

from nodeserver.engine.exceptions.plugin.plugin_internal_exceptions import  PluginMissingSourceHash
from nodeserver.engine.plugins.helpers.plugin_hasher import PluginHasher
from nodeserver.engine.plugins.helpers.plugin_manifest_helper import PluginManifestHelper
from nodeserver.engine.plugins.helpers.plugin_scanner import PluginScanner
from nodeserver.engine.plugins.helpers.plugin_version_manager import PluginVersionManager
from nodeserver.engine.plugins.plugin_compiler import PluginCompiler
from nodeserver.engine.plugins.plugin_spec_manager import PluginSpecManager
from nodeserver.engine.plugins.protocols.plugin_specs import PluginDatatypeRef
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.manifest.package_manifest import ManifestPackage

logger = logging.getLogger("nds.plugins")

class PluginManager(PluginSpecManager):
    registry: TypeRegistry

    scanner: PluginScanner
    compiler: PluginCompiler
    version_manager: PluginVersionManager

    _loaded_packages: dict[str, ManifestPackage] # package_id -> ManifestPackage
    _installed_plugins: dict[str, PluginManifest] # package_id -> PluginManifest

    _loaded_datatypes: dict[str, PluginDatatypeRef]

    def __init__(
        self,
        registry: TypeRegistry,
        scanner: Optional[PluginScanner] = None,
        compiler: Optional[PluginCompiler] = None,
        plugin_version_manager: Optional[PluginVersionManager] = None
    ):
        self.compiler = compiler or PluginCompiler(registry=registry)
        super().__init__(
            registry, scanner, plugin_version_manager
        )

    def load_or_compile_plugins(self, source_folder: Path, save_to_disk: bool = True):
        """
        Scans a folder using PluginScanner then checks plugin hashes to determine
        if plugins need to be compiled or they can just be loaded
        """
        source_folder = Path(source_folder)
        cached_plugin_list = PluginManifestHelper.load_or_create_plugin_list_cache(source_folder)

        logger.info("Loading or compiling plugins from %s...", source_folder)
        discovered_manifests = self.scanner.discover_plugins(source_folder)

        for manifest, file_path in self.resolve_plugin_load_order(discovered_manifests):
            if not manifest.source_hash:
                raise PluginMissingSourceHash(manifest.package_id)
            
            cached_hash = cached_plugin_list.cached_plugins.get(manifest.package_id)
            if not cached_hash or cached_hash != manifest.source_hash:
                self._compile_plugin_manifest(manifest, file_path, save_to_disk, assign_to_registry=True)

            self.version_manager.validate_plugin_requirements(
                manifest, self._installed_plugins
            )

            self._load_plugin_from_cache(manifest, file_path)
            
            cached_plugin_list.cached_plugins[manifest.package_id] = manifest.source_hash               
            self.index_plugin(manifest)

        PluginManifestHelper.save_plugin_list_cache(source_folder, cached_plugin_list)
        return self._installed_plugins

    def compile_plugins(
        self, 
        source_folder: Path, 
        save_to_disk: bool = True, 
        output_folder: Optional[Path] = None
    ) -> list[ManifestPackage]:
        """
        Scans a folder using PluginScanner then compiles each plugin found by it
        optionally saves ManifestPackage json (for fast boot)
        """
        source_folder = Path(source_folder)
        discovered_manifests = self.scanner.discover_plugins(source_folder)

        if save_to_disk:
            cached_plugin_list = PluginManifestHelper.load_or_create_plugin_list_cache(source_folder)

            if output_folder:
                output_folder.mkdir(parents=True, exist_ok=True)

        logger.info("Compiling plugins from %s...", source_folder)
        compiled_manifests: list[ManifestPackage] = []
        for manifest, file_path in self.resolve_plugin_load_order(discovered_manifests):
            self.version_manager.validate_plugin_requirements(
                manifest, self._installed_plugins
            )

            package = self._compile_plugin_manifest(manifest, file_path, save_to_disk, output_folder, assign_to_registry=True)
            compiled_manifests.append(package)
            self.index_plugin(manifest)
            
            manifest.source_hash = PluginHasher.calculate_plugin_hash(file_path.parent)
            cached_plugin_list.cached_plugins[manifest.package_id] = manifest.source_hash               

        if save_to_disk:
            PluginManifestHelper.save_plugin_list_cache(source_folder, cached_plugin_list)
        
        return compiled_manifests

    # Single Plugin 'Actions'

    def _compile_plugin_manifest(self, manifest: PluginManifest, file_path: Path, save_to_disk: bool = True, cache_out_folder: Optional[Path] = None, assign_to_registry: bool = False) -> ManifestPackage:
        logger.info("Compiling plugin manifest... - package_id: %s", manifest.package_id)
        modules = self.scanner.discover_modules(file_path.parent)
        self.compiler.compile_plugin_modules(manifest, modules)
        
        package: ManifestPackage = self.compiler.compile_manifest(manifest, assign_to_registry=assign_to_registry)

        if save_to_disk:
            out_folder = cache_out_folder or PluginManifestHelper.get_plugin_cache_folder(file_path.parent)
            if not out_folder.exists():
                out_folder.mkdir()
            
            PluginManifestHelper.save_package_manifest(package, out_folder)
            PluginManifestHelper.save_plugin_manifest(manifest, out_folder)

        return package
