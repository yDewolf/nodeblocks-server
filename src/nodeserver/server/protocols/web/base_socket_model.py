from pydantic import BaseModel, ConfigDict


class BaseSocketModel(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
    )
