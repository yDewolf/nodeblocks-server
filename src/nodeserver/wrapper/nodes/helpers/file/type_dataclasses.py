from typing import Annotated, Literal, Optional, Dict, List, Union, Any
from pydantic import BaseModel, ConfigDict, Field

from nodeserver.wrapper.nodes.data.node_data_types import DataTypes

class DataModel(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
    )

class SlotTypeData(DataModel):
    extends: str
    conn_whitelist: List[str]
    default_data_type: str

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)

class SlotData(DataModel):
    type: str
    data_type: Optional[DataTypes] = None

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)


class BaseNodeParameter(DataModel):
    type: Literal[DataTypes.UNKNOWN] | Literal[DataTypes.CUSTOM] | Literal[DataTypes.ARRAY]

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)

class NodeNumberParameter(DataModel):
    type: Literal[DataTypes.FLOAT] | Literal[DataTypes.UINT] | Literal[DataTypes.INT]
    range: Optional[List[Union[float, int]]] = None
    step: Optional[float] = None

class NodeFileParameter(DataModel):
    type: Literal[DataTypes.FILE] = DataTypes.FILE
    extension_filter: Optional[list[str]] = None


NodeParameterData = Annotated[
    Union[NodeNumberParameter, NodeFileParameter, BaseNodeParameter],
    Field(discriminator="type")
]

class NodeTypeData(DataModel):
    parameters: Dict[str, NodeParameterData] = Field(default_factory=dict)
    slots: Dict[str, SlotData] = Field(default_factory=dict)

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)

class TypeFile(DataModel):
    version: int
    id: str
    slot_types: Dict[str, SlotTypeData] = Field(default_factory=dict)
    node_types: Dict[str, NodeTypeData] = Field(default_factory=dict)

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)