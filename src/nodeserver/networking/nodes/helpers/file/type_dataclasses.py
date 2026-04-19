from typing import Optional, Dict, List, Union, Any
from pydantic import BaseModel, Field

class SlotTypeData(BaseModel):
    extends: str
    conn_whitelist: List[str]
    default_data_type: str

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)

class SlotData(BaseModel):
    type: str
    data_type: Optional[str] = None

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)

class NodeParameterData(BaseModel):
    type: str
    step: Optional[float] = None
    range: Optional[List[Union[float, int]]] = None

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)

class NodeTypeData(BaseModel):
    parameters: Dict[str, NodeParameterData] = Field(default_factory=dict)
    slots: Dict[str, SlotData] = Field(default_factory=dict)

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)

class TypeFile(BaseModel):
    version: int
    id: str
    slot_types: Dict[str, SlotTypeData] = Field(default_factory=dict)
    node_types: Dict[str, NodeTypeData] = Field(default_factory=dict)

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)