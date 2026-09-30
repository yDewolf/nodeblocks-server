import importlib.util
import logging
from pathlib import Path

from nodeserver.engine.plugins.helpers.plugin_hasher import PluginHasher
from nodeserver.engine.plugins.api.plugin import Plugin
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest

logger = logging.getLogger("nds.plugins")

class PluginScanner:
    def __init__(self):
        pass

    def discover_plugins(self, plugins_dir: Path) -> list[tuple[PluginManifest, Path]]:
        """
        Searches for 'plugin.py' files and returns a list of PluginManifests and their
        respective file paths.
        Automatically updates plugin's source hash.
        """

        logger.debug("Scanning for plugin manifests in %s ", plugins_dir)
        manifests: list[tuple[PluginManifest, Path]] = []
        for plugin_file in plugins_dir.rglob("plugin.py", case_sensitive=False):
            module_name = PluginScanner.make_module_name(plugin_file.parent.name)
            
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if not spec or not spec.loader:
                logger.warning("Failed to get module spec while scanning plugins. Skipping: %s", module_name)
                continue # FIXME: raise invalid plugin.py file
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type) 
                    and issubclass(attr, Plugin) 
                    and attr is not Plugin
                ):
                    manifest: PluginManifest = attr.get_manifest()
                    manifest.source_hash = PluginHasher.calculate_plugin_hash(plugin_file.parent)
                    manifests.append((
                        manifest,
                        plugin_file
                    ))

        return manifests

    def discover_modules(self, plugin_dir: Path) -> list[str]:
        logger.debug("Searching for plugin modules in %s", plugin_dir)
        module_paths: list[str] = []
        for file_path in plugin_dir.rglob("*.py"):
            if any(part.startswith(".") or part.startswith("__") for part in file_path.parts):
                continue
            
            if file_path.name in ("plugin.py", "setup.py"):
                continue

            rel_path = file_path.relative_to(plugin_dir)
            
            module_name = str(rel_path.with_suffix("")).replace("/", ".").replace("\\", ".")
            module_paths.append(module_name)
            
        return module_paths

    @staticmethod
    def make_module_name(plugin_parent_name: str) -> str:
        return f"external_plugin_{plugin_parent_name}"
