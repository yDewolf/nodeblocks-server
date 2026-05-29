
from typing import Optional

from pydantic import BaseModel, Field, field_serializer, model_validator

from nodeserver.wrapper.metadata.nodes.datatype_metadata import DataTypeMeta
from nodeserver.wrapper.metadata.nodes.node_filters import NodeCategory, NodeTag
from nodeserver.wrapper.metadata.nodes.node_metadata import NodeTypeMeta

class MetadataFileHeader(BaseModel):
    types_id: str
    types_version: int
    meta_version: int # TODO: use hashing for versions
    content_hash: Optional[str] = None
 
    # TODO: Add a iteration_version 
    # (so the actual meta_version updates only when metadata is saved from code)
    # (saved from code -> when server shuts or a less frequent update signal)
    last_modified: Optional[float] = None

    tags: dict[str, NodeTag] = Field(default_factory=dict)
    categories: dict[str, NodeCategory] = Field(default_factory=dict)

    @model_validator(mode="after")
    def resolve_internal_references(self) -> 'MetadataFileHeader':
        for tag_id, tag in self.tags.items():
            tag.tag_id = tag_id
            
        for cat_id, category in self.categories.items():
            category.category_id = cat_id

        for category in self.categories.values():
            resolved_tags = []
            # Resolve tag references
            for tag_or_id in category.default_tags:
                if isinstance(tag_or_id, str):
                    tag_obj = self.tags.get(tag_or_id)
                    if not tag_obj:
                        raise ValueError(f"Couldn't find tag of id {tag_or_id}")
                    resolved_tags.append(tag_obj)
                    continue

                resolved_tags.append(tag_or_id)
            
            category.default_tags = resolved_tags
            # Resolve super category references
            if isinstance(category.super_category, str):
                super_cat_obj = self.categories.get(category.super_category)
                if not super_cat_obj:
                    raise ValueError(f"Couldn't find super category: {category.super_category} from {category.category_id} in header")
                category.super_category = super_cat_obj

        return self

class Metadata(MetadataFileHeader):
    data_types: dict[str, DataTypeMeta]
    node_types: dict[str, NodeTypeMeta]
    
    @field_serializer("data_types")
    def serialize_data_types(self, data_types: dict[str, DataTypeMeta], _info):
        return [id for id in data_types]

    @field_serializer("node_types")
    def serialize_node_types(self, node_types: dict[str, NodeTypeMeta], _info):
        return [id for id in node_types]

class MetadataVersion(BaseModel):
    types_version: int
    meta_version: int
