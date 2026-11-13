from typing import Optional
from pydantic import BaseModel, Field

class HealthCheckRequest(BaseModel):
    version: Optional[str] = Field(default=None)
