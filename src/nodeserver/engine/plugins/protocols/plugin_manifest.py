from typing import Any, Optional, Union

from pydantic import BaseModel, Field, field_serializer, model_validator

from nodeserver.engine.plugins.protocols.plugin_datatypes import PluginDatatypeRef, PluginDatatypeSpec
from nodeserver.protocols.manifest.base_manifest import make_namespace_fqn

class PluginManifest(BaseModel):
    """
        Manifest to provide info about the plugin and its modules
    """

    package_id: str # must be the same as plugin's folder name
    version: str # SemVer

    description: Optional[str] = None
    authors: list[str] = []
    
    min_engine_version: Optional[str] = None

    dependencies: dict[str, str] = {} # ex: {"com.company.core_nodes": ">=1.0.0"}
    
    node_modules: list[str] = Field(default_factory=list) # python modules to import logic classes
    data_types: list[Union[PluginDatatypeSpec, PluginDatatypeRef]] = Field(default_factory=list)

    @field_serializer("data_types")
    def serialize_data_types(self, data_types: list[PluginDatatypeSpec]):
        return [
            PluginDatatypeRef.model_validate(
                {"namespace": data_type.namespace, "id": data_type.id, "class_path": data_type.class_path}
            ) for data_type in data_types
        ]

    @model_validator(mode="before")
    @classmethod
    def process_data_types(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        package_id = data.get("package_id")
        data_types = data.get("data_types", [])

        if not package_id or not data_types:
            return data

        processed_specs = []
        for item in data_types:
            if isinstance(item, dict):
                if not "namespace" in item:
                    item["namespace"] = package_id
                
                # if not "whitelist" in item or item["whitelist"] is None:
                #     datatype_id = item.get("id")
                #     if datatype_id:
                #         item["whitelist"] = [make_namespace_fqn(item["namespace"], datatype_id)]
                
                processed_specs.append(item)
            
            if isinstance(item, PluginDatatypeSpec):
                if item.namespace is None:
                    item.namespace = package_id
                
                if not item.whitelist and item.namespace:
                    item.whitelist = [make_namespace_fqn(item.namespace, item.id)]
                
                processed_specs.append(item)

        data["data_types"] = processed_specs
        return data
