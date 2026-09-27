import importlib.util
from pathlib import Path

from nodeserver.engine.plugins.plugin import Plugin
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest


class PluginScanner:
    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir

    def discover_plugins(self) -> list[PluginManifest]:
        manifests: list[PluginManifest] = []

        for plugin_file in self.plugins_dir.rglob("plugin.py", case_sensitive=False):
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
                        manifests.append(attr.get_manifest())

        return manifests

    @staticmethod
    def make_module_name(plugin_parent_name: str) -> str:
        return f"external_plugin_{plugin_parent_name}"
