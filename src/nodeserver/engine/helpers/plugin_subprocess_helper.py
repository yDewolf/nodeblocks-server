
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from pathlib import Path
from typing import Optional

from nodeserver.engine.engine_env import ENGINE_ENV
from nodeserver.engine.plugins.helpers.plugin_libs_manager import PluginLibsManager
from nodeserver.engine.plugins.helpers.plugin_scanner import PluginScanner
from nodeserver.engine.plugins.plugin_compiler import PluginCompiler
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.engine.utils.context_managers import scoped_sys_path
from nodeserver.engine.exceptions.plugin.plugin_internal_exceptions import PluginMissingSourceHash
from nodeserver.engine.plugins.helpers.plugin_manifest_helper import PluginManifestHelper
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.plugins.plugin_spec_manager import PluginSpecManager
from nodeserver.engine.registry.type_registry import TypeRegistry, TypeSpecRegistry

import logging

logger = logging.getLogger("nds.plugins")

def _run_indexer_task(
    plugins_folder: Path, 
    compile_core_plugins: bool = True,
    libs_dir: Optional[Path] = None
):
    full_registry = TypeRegistry()
    plugin_manager = PluginManager(
        full_registry,
        compiler=PluginCompiler(full_registry, plugins_base_package=plugins_folder.name)
    )

    paths = [plugins_folder, ENGINE_ENV.core_plugins_folder]
    if libs_dir: paths.append(libs_dir)

    with scoped_sys_path(paths):
        try:
            plugin_folders = [plugins_folder]
            if compile_core_plugins: plugin_folders.append(ENGINE_ENV.core_plugins_folder)
            plugin_manager.compile_plugins(plugin_folders, plugins_folder, save_plugin_cache=True)

            cache = PluginManifestHelper.load_or_create_plugin_list_cache(plugins_folder)
            cache.libs_fingerprint = libs_dir.name if libs_dir else None
            PluginManifestHelper.save_plugin_list_cache(plugins_folder, cache)
        
        except Exception as e:
            logger.error("Failed to compile plugins in subprocess: %s", str(e))
            raise

class PluginSubprocessHelper:
    @classmethod
    def compile_plugins_subprocess(cls, plugins_folder: Path, compile_core_plugins: bool = True, libs_dir: Optional[Path] = None):
        ctx = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=1, mp_context=ctx) as executor:
            future = executor.submit(_run_indexer_task, plugins_folder, compile_core_plugins, libs_dir)
            future.result()

    @classmethod
    def setup_and_load_plugins(cls, plugins_folder: Path, spec_manager: Optional[PluginSpecManager], load_core_plugins: bool = True, allow_install: bool = False):
        plugin_folders = [plugins_folder]
        if load_core_plugins: plugin_folders.append(ENGINE_ENV.core_plugins_folder)

        if not multiprocessing.current_process().daemon:
            scanner = PluginScanner()
            manifests = [manifest for file in plugin_folders for (manifest, _) in scanner.discover_plugins(file)]
            libs_dir = PluginLibsManager.ensure_libs(manifests, ENGINE_ENV.plugin_libs_folder, allow_install)

            if cls.needs_reindex(
                plugins_folder, libs_dir, 
                [ENGINE_ENV.core_plugins_folder] if load_core_plugins else []
            ):
                logger.info("Detected changes in plugins folder. Will recompile plugins in a subprocess... path: %s", plugins_folder)
                cls.compile_plugins_subprocess(plugins_folder, load_core_plugins, libs_dir)
                logger.info("Finished plugin recompilation")

        spec_manager = spec_manager or PluginSpecManager(TypeSpecRegistry())

        plugin_folders = [plugins_folder]
        if load_core_plugins: plugin_folders.append(ENGINE_ENV.core_plugins_folder)
        spec_manager.load_plugin_manifests(plugin_folders)
        
        return spec_manager

    @classmethod
    def needs_reindex(cls, plugins_folder: Path, libs_dir: Optional[Path], additional_plugin_folders: list[Path] = []) -> bool:
        cached_list = PluginManifestHelper.load_or_create_plugin_list_cache(plugins_folder)

        libs_fingerprint = libs_dir.name if libs_dir else None
        if cached_list.libs_fingerprint != libs_fingerprint:
            return True

        scanner = PluginScanner()
        manifests: list[tuple[PluginManifest, Path]] = []
        for folder in [plugins_folder] + additional_plugin_folders:
            discovered_manifests = scanner.discover_plugins(folder)
            manifests += discovered_manifests

        for (plugin_manifest, _)  in manifests:
            if not plugin_manifest.source_hash:
                raise PluginMissingSourceHash(plugin_manifest.package_id)
            
            cached_hash = cached_list.cached_plugins.get(plugin_manifest.package_id)
            if not cached_hash or cached_hash != plugin_manifest.source_hash:
                return True
        
        return False

    @classmethod
    def get_libs_dir(cls, plugins_folder: Path) -> Optional[Path]:
        fingerprint = PluginManifestHelper.load_or_create_plugin_list_cache(plugins_folder).libs_fingerprint
        return ENGINE_ENV.plugin_libs_folder / fingerprint if fingerprint else None
