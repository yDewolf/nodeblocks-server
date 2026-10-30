from typing import Optional

from pydantic import Field
from pydantic.dataclasses import dataclass

from nodeserver.protocols.manifest.metadata.base_meta import EngineSpecMetadata, RGBColor

@dataclass
class DataTypeStyle:
    color: Optional[RGBColor] = Field(default=None)
    backgroundColor: Optional[RGBColor] = Field(default=None)


class DataTypeMeta(EngineSpecMetadata):
    inStyle: Optional[DataTypeStyle] = Field(default_factory=DataTypeStyle)
    outStyle: Optional[DataTypeStyle] = Field(default_factory=DataTypeStyle)
