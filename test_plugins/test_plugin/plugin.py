from nodeserver.engine.plugins.plugin import Plugin
from nodeserver.engine.plugins.protocols.plugin_specs import PluginDatatypeSpec
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers

class TestPlugin(Plugin):
    manifest = PluginManifest(
        package_id="test_plugin",
        version="0.0.0"
    )
