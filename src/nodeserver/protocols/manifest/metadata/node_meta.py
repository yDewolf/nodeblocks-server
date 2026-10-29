
from pydantic import field_serializer
from nodeserver.protocols.manifest.metadata.base_meta import EngineSpecMetadata
from nodeserver.protocols.helpers.metadata.category_solvers import ResolvedCategory, ResolvedTags
from nodeserver.protocols.manifest.metadata.meta_filter import MetaCategory, MetaTag

class ParameterMeta(EngineSpecMetadata):
    pass

class SlotMeta(EngineSpecMetadata):
    pass

class NodeTypeMeta(EngineSpecMetadata):
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

DEFAULT_NODE_TAG = MetaTag(tag_id="default")
USER_INPUT_TAG = MetaTag(tag_id="input/parameter")

DEFAULT_CATEGORY = MetaCategory(category_id="Any", description="Every node that doesn't fit in a category", default_tags=[DEFAULT_NODE_TAG])
INPUT_CATEGORY = MetaCategory(category_id="Input", description="Nodes that receives user input", default_tags=[USER_INPUT_TAG])
END_CATEGORY = MetaCategory(category_id="End", description="Nodes that only receives inputs and don't output anything")

