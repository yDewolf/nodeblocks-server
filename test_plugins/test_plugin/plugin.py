from nodeserver.engine.engine_version import CURRENT_ENGINE_VERSION
from nodeserver.engine.plugins.api.plugin import Plugin
from nodeserver.engine.plugins.api.plugin_api_version import CURRENT_PLUGIN_API_VERSION
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest

class TestPlugin(Plugin):
    manifest = PluginManifest(
        package_id="test_plugin",
        plugin_version="0.0.0",
        plugin_api_version=CURRENT_PLUGIN_API_VERSION,
        engine_version=CURRENT_ENGINE_VERSION
    )
