from nodeblocks.engine.plugins.protocols.plugin_manifest import PluginManifest, EnginePluginManifest

class Plugin:
    """Any plugin must inherit this class to be managed properly"""

    manifest: PluginManifest

    @classmethod
    def get_manifest(cls) -> EnginePluginManifest:
        if not hasattr(cls, "manifest") or not isinstance(cls.manifest, PluginManifest):
            raise ValueError(f"{cls.__name__} must define 'manifest = PluginManifest(...)'")
        
        return EnginePluginManifest(**cls.manifest.__dict__)
