
from typing import Optional

from pydantic import BaseModel


class PluginListCache(BaseModel):
    # package id -> hash
    cached_plugins: dict[str, str]
    libs_fingerprint: Optional[str] = None
