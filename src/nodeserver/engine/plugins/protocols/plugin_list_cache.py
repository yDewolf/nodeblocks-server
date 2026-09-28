
from pydantic import BaseModel


class PluginListCache(BaseModel):
    # package id -> hash
    cached_plugins: dict[str, str]
