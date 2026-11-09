from pydantic import Field

from nodeserver.engine.engine_version import CURRENT_ENGINE_VERSION
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest

ARCHIVE_FORMAT_VERSION = 1

# related to plugin zips
class PluginArchive(PluginManifest):
    format_version: int = Field(default=ARCHIVE_FORMAT_VERSION)
    built_with_engine: str = Field(default=CURRENT_ENGINE_VERSION)


ARCHIVE_EXTENSION = ".nbplugin"
ARCHIVE_INFO_NAME = "nbplugin.json"

STATE_DIR_NAME = ".nbplugin-state"
