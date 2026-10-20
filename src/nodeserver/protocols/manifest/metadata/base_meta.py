from typing import Optional

from pydantic import BaseModel


class BaseMetadata(BaseModel):
    capitalized_name: str
    brief: str = ""
    
    description: str = ""


class EngineSpecMetadata(BaseMetadata):
    usages: Optional[list[str]] = None
