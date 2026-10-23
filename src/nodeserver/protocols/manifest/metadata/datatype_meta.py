from typing import Optional

from pydantic import Field

from nodeserver.protocols.manifest.metadata.base_meta import EngineSpecMetadata, RGBColor


class DataTypeMeta(EngineSpecMetadata):
    color: Optional[RGBColor] = Field(default=None)
