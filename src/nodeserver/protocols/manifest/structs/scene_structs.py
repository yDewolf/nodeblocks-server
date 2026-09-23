from pydantic import BaseModel


class Vector2(BaseModel):
    x: float = 0.0
    y: float = 0.0
    
    @classmethod
    def from_dict(cls, data: dict, **kwargs):
        return cls.model_validate({**data, **kwargs})
