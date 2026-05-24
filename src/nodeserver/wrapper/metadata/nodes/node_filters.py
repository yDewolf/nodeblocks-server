
from typing import Optional, Union

from pydantic import BaseModel, Field, field_serializer


class NodeTag(BaseModel):
    tag_id: str = Field(default="", exclude=True)
    description: str = ""

class NodeCategory(BaseModel):
    category_id: str = Field(default="", exclude=True)
    description: str = ""
    super_category: Optional[Union['NodeCategory', str]] = None
    default_tags: list[Union[NodeTag, str]] = []
    
    @field_serializer("default_tags")
    def serialize_tags(self, default_tags: Optional[list[NodeTag]], _info):
        return [(tag if isinstance(tag, str) else tag.tag_id) for tag in default_tags] if default_tags else []
