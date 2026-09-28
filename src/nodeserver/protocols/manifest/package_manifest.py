from nodeserver.protocols.manifest.base_manifest import DataModel
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec
from nodeserver.protocols.manifest.node.node_manifest import NodeTypeSpec

# Describes specs NodeTypeSpec, DataTypeSpec
# everything the client must know about to setup NodeTypeSelector etc

class ManifestPackage(DataModel):
    # format: Optional[int] = None # FIXME on client -> remove this
    
    # TODO: implement package versioning
    version: str # FIXME on client: int -> str
    package_id: str # FIXME on client: id -> package_id
    
    data_types: dict[str, DataTypeSpec]
    # slot_types: dict[str, str] # FIXME on client -> remove this
    node_types: dict[str, NodeTypeSpec]

    def serialize(self) -> dict:
        return self.model_dump(by_alias=True)
