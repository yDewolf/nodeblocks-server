from typing import Optional

from pydantic import BaseModel


class PluginManifest(BaseModel):
    """
        Manifest to provide info about the plugin and its modules
    """

    package_id: str
    version: str # SemVer

    description: Optional[str] = None
    authors: list[str] = []
    
    min_engine_version: Optional[str] = None

    dependencies: dict[str, str] = {} # ex: {"com.company.core_nodes": ">=1.0.0"}
    
    node_modules: list[str] # python modules to import logic classes
