from typing import Annotated, Literal, Optional, Dict, List, Union, Any
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

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
    default: Optional[Any] = None

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)

class NodeNumberParameter(BaseNodeParameter):
    type: Literal[DefaultDataTypes.FLOAT] | Literal[DefaultDataTypes.UINT] | Literal[DefaultDataTypes.INT]
    range: Optional[List[Union[float, int]]] = None
    step: Optional[float] = None

class BooleanParameter(BaseNodeParameter):
    type: Literal[DefaultDataTypes.BOOLEAN]

class NodeOptionParameter(BaseNodeParameter):
    type: Literal[DefaultDataTypes.OPTIONS]
    
    option_type: DefaultDataTypes
    options: list[Any]

class NodeFileParameter(BaseNodeParameter):
    type: Literal[DefaultDataTypes.FILE] = DefaultDataTypes.FILE
    extension_filter: Optional[list[str]] = None


NodeParameterData = Annotated[
    Union[NodeNumberParameter, BooleanParameter, NodeFileParameter, NodeOptionParameter, BaseNodeParameter],
    Field(discriminator="type")
]

NodeParameterDataAdapter = TypeAdapter(NodeParameterData)

class NodeTypeData(DataModel):
    _base_metadata: Optional[NodeTypeMeta] = Field(exclude=True)
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