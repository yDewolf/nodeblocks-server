from typing import Optional

from pydantic import BaseModel, Field, field_serializer
from nodeserver.wrapper.metadata.base_metadata import BaseMetadata

# TODO: Move this to a node_filtering file
class NodeTag(BaseModel):
    tag_id: str = Field(exclude=True)
    description: str = ""

# TODO: Move this to a node_filtering file
class NodeCategory(BaseModel):
    category_id: str = Field(exclude=True)
    description: str = ""
    super_category: Optional['NodeCategory'] = None
    default_tags: Optional[list[NodeTag]] = []
    
    @field_serializer("default_tags")
    def serialize_tags(self, default_tags: Optional[list[NodeTag]], _info):
        return [tag.tag_id for tag in default_tags] if default_tags else []

class ParameterMeta(BaseMetadata):
    pass

class SlotMeta(BaseMetadata):
    pass

class NodeTypeMeta(BaseMetadata):
    """
        Every attribute of this class will be used as a default value for the generated
        metadata file. These attributes will be overridden by the metadata file content (if it exists)
    """
    category: NodeCategory
    """
        A default category can be set in Node._metadata <br>
        it will be auto overridden when a proper metadata file is edited
    """
    
    tags: list[NodeTag] = []
    """
        Default tags can be set in Node._metadata <br>
        it will be auto overridden when a proper metadata file is edited
    """
    parameter_meta: dict[str, ParameterMeta] = {}
    slot_meta: dict[str, SlotMeta] = {}
    
    @field_serializer("category")
    def serialize_category(self, category: NodeCategory, _info):
        return category.category_id

    @field_serializer("tags")
    def serialize_tags(self, tags: list[NodeTag], _info):
        tag_ids = [tag.tag_id for tag in tags]
        return tag_ids


DEFAULT_NODE_TAG = NodeTag(tag_id="default")
USER_INPUT_TAG = NodeTag(tag_id="input/parameter")

DEFAULT_CATEGORY = NodeCategory(category_id="Any", description="Every node that doesn't fit in a category", default_tags=[DEFAULT_NODE_TAG])
INPUT_CATEGORY = NodeCategory(category_id="Input", description="Nodes that receives user input", default_tags=[USER_INPUT_TAG])
END_CATEGORY = NodeCategory(category_id="End", description="Nodes that only receives inputs and don't output anything")

