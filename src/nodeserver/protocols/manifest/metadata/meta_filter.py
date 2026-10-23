
from typing import Optional, Union

from pydantic import BaseModel, Field, field_serializer

from nodeserver.protocols.manifest.metadata.base_meta import RGBColor


class MetaTag(BaseModel):
    tag_id: str = Field(default="", exclude=True)
    description: str = ""

class MetaCategory(BaseModel):
    category_id: str = Field(default="", exclude=True)
    description: str = ""
    super_category: Optional[Union['MetaCategory', str]] = None
    default_tags: list[Union[MetaTag, str]] = []

    color: Optional[RGBColor] = Field(default=None)
 
    @field_serializer("default_tags")
    def serialize_tags(self, default_tags: Optional[list[MetaTag]], _info):
        return [(tag if isinstance(tag, str) else tag.tag_id) for tag in default_tags] if default_tags else []
