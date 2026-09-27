import importlib.util
from pathlib import Path

from nodeserver.engine.plugins.plugin import Plugin
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest


class PluginScanner:
    def __init__(self):
        pass

    def discover_plugins(self, plugins_dir: Path) -> list[tuple[PluginManifest, Path]]:
        manifests: list[tuple[PluginManifest, Path]] = []
        for plugin_file in plugins_dir.rglob("plugin.py", case_sensitive=False):
            module_name = PluginScanner.make_module_name(plugin_file.parent.name)
            
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type) 
                        and issubclass(attr, Plugin) 
                        and attr is not Plugin
                    ):
                        manifests.append((
                            attr.get_manifest(),
                            plugin_file
                        ))

        return manifests

    def discover_modules(self, plugin_dir: Path) -> list[str]:
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
