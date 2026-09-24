from typing import Annotated, Literal, Optional, List, Type, Union, Any
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes
from nodeserver.protocols.enums.datatype_enums import DefaultRenderers

class DataModel(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
    )

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)

class DataTypeSpec(DataModel):
    # TODO: implementar estilos de DataType com cor, etc (provavelmente nos baglh de metadata)
    id: str
    namespace: str

    base_id: Optional[DefaultDataTypes] # FIXME on client: base -> base_id
    default_renderer: DefaultRenderers # TODO: Implement proper renderer solver
    whitelist: list[str] = Field(default_factory=list)

    @property
    def fqn(self) -> str:
        return f"{self.namespace}:{self.id}"

# Parameter Spec Definition

class BaseParameterSpec(DataModel):
    type: Literal[DefaultDataTypes.UNKNOWN] | Literal[DefaultDataTypes.CUSTOM] | Literal[DefaultDataTypes.ARRAY]
    label: Optional[str] = Field(default=None, exclude=True)
    default: Optional[Any] = None
    required: bool = False

    # FIXME: this field should be excluded only when sending to client
    raw_io_type: Optional[Type[Any]] = Field(default=None, exclude=True)

class _NumberParameter(BaseParameterSpec):
    type: Literal[DefaultDataTypes.FLOAT] | Literal[DefaultDataTypes.UINT] | Literal[DefaultDataTypes.INT]
    range: Optional[List[Union[float, int]]] = None
    step: Optional[float] = None


class FloatParam(_NumberParameter):
    type: Literal[DefaultDataTypes.FLOAT]

class IntParam(_NumberParameter):
    type: Literal[DefaultDataTypes.INT] | Literal[DefaultDataTypes.UINT]

class BooleanParam(BaseParameterSpec):
    type: Literal[DefaultDataTypes.BOOLEAN]

class OptionParam(BaseParameterSpec):
    type: Literal[DefaultDataTypes.OPTIONS]

    option_type: DefaultDataTypes
    options: list[Any]

class FileParam(BaseParameterSpec):
    type: Literal[DefaultDataTypes.FILE] = DefaultDataTypes.FILE
    extension_filter: Optional[list[str]] = None


class GenericParameterSpec(BaseParameterSpec):
    type: Literal[DefaultDataTypes.UNKNOWN] | Literal[DefaultDataTypes.CUSTOM] | Literal[DefaultDataTypes.ARRAY]


ParameterSpec = Annotated[
    Union[FloatParam, IntParam, BooleanParam, FileParam, OptionParam, GenericParameterSpec],
    Field(discriminator="type")
]

ParameterSpecAdapter = TypeAdapter(ParameterSpec)
