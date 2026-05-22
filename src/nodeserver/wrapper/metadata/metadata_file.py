import os
from typing import Optional

from pydantic import BaseModel, field_serializer

from nodeserver.wrapper.metadata.nodes.datatype_metadata import DataTypeMeta
from nodeserver.wrapper.metadata.nodes.node_metadata import NodeTypeMeta
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import TypeFile
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import TypeFileReader

METADATA_EXTENSION = ".json"
METADATA_INDENT = 1

class MetadataFileHeader(BaseModel):
    types_id: str
    meta_version: int # TODO: use hashing for versions

class Metadata(MetadataFileHeader):
    data_types: dict[str, DataTypeMeta]
    node_types: dict[str, NodeTypeMeta]
    
    @field_serializer("data_types")
    def serialize_data_types(self, data_types: dict[str, DataTypeMeta], _info):
        return [id for id in data_types]

    @field_serializer("node_types")
    def serialize_node_types(self, node_types: dict[str, DataTypeMeta], _info):
        return [id for id in node_types]

class MetadataFile:
    metadata: Optional[Metadata] = None
    
    def __init__(self) -> None:
        pass

    @classmethod
    def new(cls, type_reader: TypeFileReader) -> "MetadataFile":
        metadata_file = MetadataFile()
        metadata_file.set_from_types(type_reader)
        return metadata_file

    def save_to_folder(self, folder_path: str):
        if not self.metadata:
            raise Exception("No metadata to save")
        
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
    
        if not os.path.isdir(folder_path):
            raise Exception("Folder path should lead to a folder")

        node_meta_path = os.path.join(folder_path, "nodes")
        datatypes_path = os.path.join(folder_path, "datatypes")
        if not os.path.exists(node_meta_path): os.mkdir(node_meta_path)
        if not os.path.exists(datatypes_path): os.mkdir(datatypes_path)
        
        for type_id, node_meta in self.metadata.node_types.items():
            # TODO: Ensure type id doesn't contain any special characters
            file_path = os.path.join(node_meta_path, f"{type_id}{METADATA_EXTENSION}")
            with open(file_path, "w") as file:
                file.write(node_meta.model_dump_json(indent=METADATA_INDENT))
        
        slotio_types: dict[str, list[str]] = {}
        for type_id in self.metadata.data_types:
            # TODO: Ensure type id doesn't contain any special characters
            splitted_type_id = type_id.split(":")
            slotio_type = splitted_type_id[0]
            if not slotio_types.__contains__(slotio_type):
                slotio_types[slotio_type] = []
            
            slotio_types[slotio_type] += splitted_type_id[1:] or []
        
        for slotio_type, subtypes in slotio_types.items():
            slotio_folder_path = os.path.join(datatypes_path, slotio_type)
            if not os.path.isdir(slotio_folder_path): os.mkdir(slotio_folder_path)
            if len(subtypes) == 0: subtypes.append("default")
            for subtype in subtypes:
                type_id = f"{slotio_type}:{subtype}"
                subtype_file_path = os.path.join(slotio_folder_path, f"{subtype}{METADATA_EXTENSION}")
                subtype_meta = self.metadata.data_types.get(type_id)
                if not subtype_meta: 
                    raise Exception(f"Failed to find corresponding metadata for datatype {type_id}")
                
                with open(subtype_file_path, "w") as file:
                    file.write(subtype_meta.model_dump_json(indent=METADATA_INDENT))                
        
        header_file_path = os.path.join(folder_path, f"metadata{METADATA_EXTENSION}")
        with open(header_file_path, "w") as file:
            file.write(self.metadata.model_dump_json(indent=METADATA_INDENT))
        
    def set_from_types(self, type_reader: TypeFileReader):
        self.metadata = MetadataFile.generate_meta_model(type_reader)
    
    @staticmethod
    def generate_meta_model(type_reader: TypeFileReader) -> Metadata:
        if not type_reader._node_types_id: 
            raise Exception(f"TypeFile is missing node type id. Referred reader: {type_reader}")
        
        datatype_meta = {}
        for type_id, data_type in type_reader.data_types.items():
            meta = DataTypeMeta(
                capitalized_name=type_id, # TODO make an auto capitalizer func
                description=""
            )
            datatype_meta[type_id] = meta
        
        nodetype_meta = {}
        for type_id, constructor in type_reader.node_constructors.items():
            # TODO: auto generate some of the metadata here if it doesn't exist in the constructor
            meta = NodeTypeMeta(
                capitalized_name=constructor._metadata.capitalized_name,
                description=constructor._metadata.description,
                category=constructor._metadata.category,
                tags=constructor._metadata.tags,
                slot_meta=constructor._metadata.slot_meta
            )
            nodetype_meta[type_id] = meta
        
        metadata = Metadata(
            types_id=type_reader._node_types_id,
            meta_version=0,
            data_types=datatype_meta,
            node_types=nodetype_meta 
        )
        return metadata