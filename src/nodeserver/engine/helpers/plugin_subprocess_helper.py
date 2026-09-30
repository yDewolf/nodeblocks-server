
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from pathlib import Path
from typing import Optional

from nodeserver.engine.plugins.plugin_compiler import PluginCompiler
from nodeserver.engine.utils.context_managers import scoped_sys_path
from nodeserver.engine.exceptions.plugin.plugin_internal_exceptions import PluginMissingSourceHash
from nodeserver.engine.plugins.helpers.plugin_manifest_helper import PluginManifestHelper
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.plugins.plugin_spec_manager import PluginSpecManager
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.engine.registry.type_registry import TypeRegistry, TypeSpecRegistry

import logging

logger = logging.getLogger("nds.plugins")

def _run_indexer_task(plugins_folder: Path):
    full_registry = TypeRegistry()
    plugin_manager = PluginManager(
        full_registry,
        compiler=PluginCompiler(full_registry, plugins_base_package=plugins_folder.name)
    )

    with scoped_sys_path(plugins_folder):
        plugin_manager.compile_plugins(plugins_folder, save_to_disk=True)


class PluginSubprocessHelper:
    @classmethod
    def compile_plugins_subprocess(cls, plugins_folder: Path):
        ctx = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=1, mp_context=ctx) as executor:
            future = executor.submit(_run_indexer_task, plugins_folder)
            future.result()

    @classmethod
    def setup_and_load_plugins(cls, plugins_folder: Path, spec_manager: Optional[PluginSpecManager]):
        if cls.needs_reindex(plugins_folder):
            logger.info("Detected changes in plugins folder. Will recompile plugins in a subprocess... path: %s", plugins_folder)
            cls.compile_plugins_subprocess(plugins_folder)                
            logger.info("Finished plugin recompilation")

        spec_manager = spec_manager or PluginSpecManager(TypeSpecRegistry())
        spec_manager.load_plugin_manifests(plugins_folder)
        
        return spec_manager


    @classmethod
    def needs_reindex(cls, plugins_folder: Path) -> bool:
        cached_list = PluginManifestHelper.load_or_create_plugin_list_cache(plugins_folder)

        manifests: list[PluginManifest] = []
        for file in PluginManifestHelper.iterate_plugin_cache_files(plugins_folder):
            manifest = PluginManifestHelper.load_plugin_manifest(file)
            manifests.append(manifest)
        
        for plugin_manifest in manifests:
            if not plugin_manifest.source_hash:
                raise PluginMissingSourceHash(plugin_manifest.package_id)
            
            cached_hash = cached_list.cached_plugins.get(plugin_manifest.package_id)
            if not cached_hash or cached_hash != plugin_manifest.source_hash:
                return True
        
        return False
