from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest

class Plugin:
    """Any plugin must inherit this class to be managed properly"""

    manifest: PluginManifest

    @classmethod
    def get_manifest(cls) -> PluginManifest:
        if not hasattr(cls, "manifest") or not isinstance(cls.manifest, PluginManifest):
            raise ValueError(f"{cls.__name__} must define 'manifest = PluginManifest(...)'")
        
        return cls.manifest
