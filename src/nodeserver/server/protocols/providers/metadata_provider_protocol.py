from abc import abstractmethod
from typing import Protocol

from nodeserver.protocols.manifest.metadata.datatype_meta import DataTypeMeta
from nodeserver.protocols.manifest.metadata.metadata_header import MetadataManifest, MetadataHeader
from nodeserver.protocols.manifest.metadata.node_meta import NodeTypeMeta


class IMetadataProvider(Protocol):
    @abstractmethod
    def package_has_metadata(self, package_id: str) -> bool: pass

    @abstractmethod
    def get_metadata_manifest(self, package_id: str) -> MetadataManifest: pass

    @abstractmethod
    def get_metadata_header(self, package_id: str) -> MetadataHeader: pass

    @abstractmethod
    def get_metadata_datatypes(self, package_id: str) -> dict[str, DataTypeMeta]: pass

    @abstractmethod
    def get_metadata_nodetypes(self, package_id: str) -> dict[str, NodeTypeMeta]: pass

    @abstractmethod
    def save_package_metadata(self, metadata: MetadataManifest): pass
