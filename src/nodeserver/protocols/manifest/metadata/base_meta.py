from typing import Optional

from pydantic import BaseModel
from pydantic.dataclasses import dataclass


class BaseMetadata(BaseModel):
    capitalized_name: str
    brief: Optional[str] = None
    
    description: str = ""

class EngineSpecMetadata(BaseMetadata):
    usages: Optional[list[str]] = None


@dataclass
class RGBColor:
    # These value should be between 0 and 255
    r: int
    g: int
    b: int
