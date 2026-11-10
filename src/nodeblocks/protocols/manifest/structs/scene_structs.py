from pydantic import BaseModel


class Vector2(BaseModel):
    x: float = 0.0
    y: float = 0.0
