
from pydantic import field_serializer
from nodeserver.wrapper.metadata.base_metadata import BaseMetadata
from nodeserver.wrapper.metadata.helpers.category_solvers import ResolvedCategory, ResolvedTags
from nodeserver.wrapper.metadata.nodes.node_filters import NodeCategory, NodeTag

class ParameterMeta(BaseMetadata):
    pass

class SlotMeta(BaseMetadata):
    pass

class NodeTypeMeta(BaseMetadata):
    """
        Every attribute of this class will be used as a default value for the generated
        metadata file. These attributes will be overridden by the metadata file content (if it exists)
    """
    category: ResolvedCategory
    """
        A default category can be set in Node._metadata <br>
        it will be auto overridden when a proper metadata file is edited
    """
    
    tags: ResolvedTags = []
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

