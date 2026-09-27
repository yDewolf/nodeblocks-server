from pydantic import BaseModel


class NodeCacheEntry(BaseModel):
    class_path: str
    required_datatypes: list[str] # datatype fqn list
