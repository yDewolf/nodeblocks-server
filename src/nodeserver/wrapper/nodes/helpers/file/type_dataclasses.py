from typing import Annotated, Literal, Optional, Dict, List, Type, Union, Any
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_serializer, model_validator

from nodeserver.wrapper.nodes.data.node_data_types import DefaultDataTypes, DefaultRenderers
from nodeserver.wrapper.metadata.nodes.node_metadata import NodeTypeMeta

class DataModel(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
    )

class DataTypeData(DataModel):
    base: Optional[DefaultDataTypes]
    default_renderer: DefaultRenderers # TODO: Implement proper renderer solver
    whitelist: list[str]


class SlotTypeData(DataModel):
    data_type_id: str
    
    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)

class SlotData(DataModel):
    type: str
    data_type: Optional[DefaultDataTypes] = None
    max_connections: Optional[int] = None # 0 -> Doesn't have a max
    is_input: bool

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)


class BaseNodeParameter(DataModel):
    type: Literal[DefaultDataTypes.UNKNOWN] | Literal[DefaultDataTypes.CUSTOM] | Literal[DefaultDataTypes.ARRAY]
    label: Optional[str] = Field(default=None, exclude=True)
    default: Optional[Any] = None
    required: bool = False

    # FIXME: this field should be excluded only when sending to client
    raw_io_type: Optional[Type[Any]] = Field(default=None, exclude=True)

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)

class _NodeNumberParameter(BaseNodeParameter):
    type: Literal[DefaultDataTypes.FLOAT] | Literal[DefaultDataTypes.UINT] | Literal[DefaultDataTypes.INT]
    range: Optional[List[Union[float, int]]] = None
    step: Optional[float] = None

class NodeFloatParam(_NodeNumberParameter):
    type: Literal[DefaultDataTypes.FLOAT]
    # raw_io_type: Type[Any] = float

class NodeIntParam(_NodeNumberParameter):
    type: Literal[DefaultDataTypes.INT] | Literal[DefaultDataTypes.UINT]
    # raw_io_type: Type[Any] = int

class BooleanParameter(BaseNodeParameter):
    type: Literal[DefaultDataTypes.BOOLEAN]
    # raw_io_type: Type[Any] = bool

class NodeOptionParameter(BaseNodeParameter):
    type: Literal[DefaultDataTypes.OPTIONS]
    # raw_io_type: Type[Any] = str

    option_type: DefaultDataTypes
    options: list[Any]

class NodeFileParameter(BaseNodeParameter):
    type: Literal[DefaultDataTypes.FILE] = DefaultDataTypes.FILE
    # raw_io_type: Type[Any] = str
    extension_filter: Optional[list[str]] = None


NodeParameterData = Annotated[
    Union[NodeFloatParam, NodeIntParam, BooleanParameter, NodeFileParameter, NodeOptionParameter, BaseNodeParameter],
    Field(discriminator="type")
]

NodeParameterDataAdapter = TypeAdapter(NodeParameterData)

class NodeTypeData(DataModel):
    default_metadata: Optional[NodeTypeMeta] = Field(default=None, exclude=True)
    parameters: Dict[str, NodeParameterData]
    slots: Dict[str, SlotData]

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)

class TypeFile(DataModel):
    format: Optional[int] = None
    version: int
    id: str
    
    data_types: Dict[str, DataTypeData]
    slot_types: Dict[str, SlotTypeData]
    node_types: Dict[str, NodeTypeData]

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)