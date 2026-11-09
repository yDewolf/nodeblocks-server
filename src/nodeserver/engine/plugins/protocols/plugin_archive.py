from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from nodeserver.engine.engine_version import CURRENT_ENGINE_VERSION
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest

ARCHIVE_FORMAT_VERSION = 1

# related to plugin zips
class PluginArchive(PluginManifest):
    format_version: int = Field(default=ARCHIVE_FORMAT_VERSION)
    built_with_engine: str = Field(default=CURRENT_ENGINE_VERSION)


DEFAULT_ARCHIVE_EXTENSION = ".nbplugin"
ARCHIVE_EXTENSIONS = (DEFAULT_ARCHIVE_EXTENSION, ".nbplugin.zip")
ARCHIVE_INFO_NAME = "nbplugin.json"

STATE_DIR_NAME = ".nbplugin-state"


class ArchiveStatuses(StrEnum):
    EXTRACTING = "extracting"
    COMPLETE = "complete"


class PluginArchiveState(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    package_id: str
    plugin_version: str
    
    archive_name: str
    archive_sha256: str

    status: ArchiveStatuses

class EnginePluginArchive(PluginArchive):
    path: Path
