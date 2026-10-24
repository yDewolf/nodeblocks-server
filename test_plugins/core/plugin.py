from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.engine.plugins.api.plugin import Plugin


class CorePlugin(Plugin):
    manifest = PluginManifest(
        package_id="core",
        plugin_version="0.1.0",
        description="Description for Core",
        authors=["yDewolf"],
        engine_version=f">=0.1.0", # Current Engine Version
        plugin_api_version=f">=1.1.0", # Current Plugin API Version
        dependencies={},
    )
