
from nodeserver.wrapper.metadata.metadata_file import MetadataFile
from nodeserver.wrapper.metadata.metadata_header import Metadata, MetadataVersion
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import TypeFile
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import TypeFileReader


class MetadataManager:
    indexed_metadata: dict[str, MetadataFile]
    def __init__(self) -> None:
        self.indexed_metadata = {}

    def index_metadata_for_type(self, type_reader: TypeFileReader):
        if not type_reader._node_types_id: 
            raise Exception("TypeReader doesn't have _node_types_id set")

        if self.indexed_metadata.__contains__(type_reader._node_types_id):
            return

        metadata = MetadataFile.new(type_reader, True)
        self.indexed_metadata[type_reader._node_types_id] = metadata


    def keep_metadata_synced(self) -> list[str]:
        """
            Returns a list with the id of Types that have changes on their metadata.
        """
        updated_metadata: list[str] = []
        for type_id, metadata_file in self.indexed_metadata.items():
            if metadata_file.has_modifications_on_disk():
                updated_metadata.append(type_id)
                metadata_file.reload_from_disk(only_if_modified=False)
        
        return updated_metadata

    def get_metadata_version(self, type_id: str) -> MetadataVersion:
        metadata_file = self.indexed_metadata.get(type_id, None)
        if not metadata_file:
            raise Exception(f"Couldn't find metadata related to type id: {type_id}")
        
        if not metadata_file.metadata:
            raise Exception(f"Metadata file (type_id: {type_id}) doesn't have a metadata loaded")

        return MetadataVersion(
            types_version=metadata_file.metadata.types_version,
            meta_version=metadata_file.metadata.meta_version
        )