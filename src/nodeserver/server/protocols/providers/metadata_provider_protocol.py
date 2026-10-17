from abc import abstractmethod
from typing import Protocol

from nodeserver.protocols.manifest.metadata.metadata_header import Metadata, MetadataManifest


class IMetadataProvider(Protocol):
    @abstractmethod
    def get_package_metadata(self, package_id: str) -> Metadata: pass

    @abstractmethod
    def get_package_metadata_manifest(self, package_id: str) -> MetadataManifest: pass

    @abstractmethod
    def save_package_metadata(self, metadata: Metadata): pass
