from typing import Optional

from pydantic import BaseModel


class BaseMetadata(BaseModel):
    capitalized_name: str
    brief: Optional[str] = None
    
    description: str = ""


class EngineSpecMetadata(BaseMetadata):
    usages: Optional[list[str]] = None
