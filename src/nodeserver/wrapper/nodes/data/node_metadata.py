from typing import Optional

from pydantic import BaseModel

class NodeTag(BaseModel):
    tag_name: str
    description: Optional[str] = "No Description"

class NodeCategory(BaseModel):
    super_category: Optional['NodeCategory'] = None
    name: str
    description: str
    default_tags: Optional[list[NodeTag]] = []

class NodeMetadata(BaseModel):
    category: NodeCategory
    
    capitalized_type: str # Set to "" so it assigns based on the type registry
    tags: Optional[list[NodeTag]] = []


DEFAULT_NODE_TAG = NodeTag(tag_name="default")
USER_INPUT_TAG = NodeTag(tag_name="input/parameter")

DEFAULT_CATEGORY = NodeCategory(name="Any", description="Every node that doesn't fit in a category", default_tags=[DEFAULT_NODE_TAG])
INPUT_CATEGORY = NodeCategory(name="Input", description="Nodes that receives user input", default_tags=[USER_INPUT_TAG])
END_CATEGORY = NodeCategory(name="End", description="Nodes that only receives inputs and don't output anything")

