from typing import Optional

from pydantic import BaseModel

from nodeserver.wrapper.metadata.base_metadata import BaseMetadata

class NodeTag(BaseModel):
    tag_name: str
    description: Optional[str] = "No Description"

class NodeCategory(BaseModel):
    super_category: Optional['NodeCategory'] = None
    name: str
    description: str
    default_tags: Optional[list[NodeTag]] = []

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


DEFAULT_NODE_TAG = NodeTag(tag_name="default")
USER_INPUT_TAG = NodeTag(tag_name="input/parameter")

DEFAULT_CATEGORY = NodeCategory(name="Any", description="Every node that doesn't fit in a category", default_tags=[DEFAULT_NODE_TAG])
INPUT_CATEGORY = NodeCategory(name="Input", description="Nodes that receives user input", default_tags=[USER_INPUT_TAG])
END_CATEGORY = NodeCategory(name="End", description="Nodes that only receives inputs and don't output anything")

