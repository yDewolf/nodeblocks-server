from pydantic import BaseModel


class BaseMetadata(BaseModel):
    capitalized_name: str
    description: str = ""

    