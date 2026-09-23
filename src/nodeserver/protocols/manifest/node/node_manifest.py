from typing import Dict, Optional

from pydantic import Field

from nodeserver.engine.protocols.datatype.node_data_types import DefaultDataTypes
from nodeserver.protocols.manifest.metadata.node_meta import NodeTypeMeta
from nodeserver.protocols.manifest.node.datatypes import DataModel, DataTypeData, ParameterSpec


class NodeSlotSpec(DataModel):
    type: str
    data_type: Optional[DefaultDataTypes] = None

    max_connections: Optional[int] = None # 0 -> Doesn't have a max
    is_input: bool


class NodeTypeSpec(DataModel):
    # FIXME: talvez isso aqui seja desnecessário
    default_metadata: Optional[NodeTypeMeta] = Field(default=None, exclude=True)

    parameters: Dict[str, ParameterSpec]
    slots: Dict[str, NodeSlotSpec]

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)


class ManifestPackage(DataModel):
    format: Optional[int] = None
    version: int
    package_id: str # FIXME on client: id -> package_id
    
    data_types: Dict[str, DataTypeData]
    slot_types: Dict[str, str]
    node_types: Dict[str, NodeTypeSpec]

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)
