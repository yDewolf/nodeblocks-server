from typing import Dict, Optional

from pydantic import Field

from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes
from nodeserver.protocols.manifest.base_manifest import DataModel, NamespaceModel
from nodeserver.protocols.manifest.metadata.node_meta import NodeTypeMeta
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec, ParameterSpec


class NodeSlotSpec(DataModel):
    # type: str # FIXME on client: remove this  
    data_type_id: str # FIXME on client: data_type -> data_type_id

    # TODO: output slots should default to max_connections = 0
    max_connections: int = Field(default=1) # 0 -> Doesn't have a max
    required: bool = False # Defines if this slot must be connected to process the node
    is_input: bool


class NodeTypeSpec(NamespaceModel):
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
    
    data_types: Dict[str, DataTypeSpec]
    slot_types: Dict[str, str]
    node_types: Dict[str, NodeTypeSpec]

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)
