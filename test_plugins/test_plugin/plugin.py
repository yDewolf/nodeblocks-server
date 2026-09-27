from nodeserver.engine.plugins.plugin import Plugin
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest


class TestPlugin(Plugin):
    manifest = PluginManifest(
        package_id="test.plugin",
        version="0.0.0",

        node_modules=[
            "test_nodes"
        ]
    )
