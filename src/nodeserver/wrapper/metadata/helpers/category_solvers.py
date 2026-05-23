from typing import Annotated, Any

from pydantic import BeforeValidator, PlainSerializer, ValidationInfo
from nodeserver.wrapper.metadata.nodes.node_filters import NodeCategory, NodeTag

def solve_category(cat_value: Any, info: ValidationInfo) -> Any:
    if isinstance(cat_value, str) and info.context:
        categories = info.context.get("categories", {})
        if isinstance(categories, dict):
            return categories.get(cat_value, cat_value)
    
    return cat_value

def serialize_category(category: NodeCategory) -> str:
    return category.category_id

def solve_tags_list(tag_value: Any, info: ValidationInfo) -> Any:
    if isinstance(tag_value, list) and info.context:
        tags_pool = info.context.get("tags", {})
        if isinstance(tags_pool, dict):
            solved_tags: list = []
            for tag_id in tag_value:
                if isinstance(tag_id, str):
                    solved_tags.append(tags_pool.get(tag_id))        
                    continue

                solved_tags.append(tag_id)

            return solved_tags                
    
    return tag_value

def serialize_tag_list(tags: list[NodeTag]) -> list[str]:
    return [tag.tag_id for tag in tags]

ResolvedCategory = Annotated[
    NodeCategory,
    BeforeValidator(solve_category),
    PlainSerializer(serialize_category)
]

ResolvedTags = Annotated[
    list[NodeTag],
    BeforeValidator(solve_tags_list),
    PlainSerializer(serialize_tag_list)
]