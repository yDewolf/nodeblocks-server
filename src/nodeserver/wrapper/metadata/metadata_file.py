import json
import os
from typing import Any, Optional

from pydantic import BaseModel, Field, field_serializer, field_validator, model_validator

from nodeserver.api.utils.file_utils import get_project_root
from nodeserver.wrapper.metadata.nodes.datatype_metadata import DataTypeMeta
from nodeserver.wrapper.metadata.nodes.node_metadata import NodeCategory, NodeTag, NodeTypeMeta, ParameterMeta, SlotMeta
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import TypeFileReader

METADATA_EXTENSION = ".json"
METADATA_INDENT = 1

ROOT_METADATA_PATH = os.path.join(get_project_root(), "metadata")

class MetadataFileHeader(BaseModel):
    types_id: str
    meta_version: int # TODO: use hashing for versions
    
    tags: dict[str, NodeTag] = Field(default_factory=dict)
    categories: dict[str, NodeCategory] = Field(default_factory=dict)

    @model_validator(mode="after")
    def resolve_internal_references(self) -> 'MetadataFileHeader':
        for tag_id, tag in self.tags.items():
            tag.tag_id = tag_id
            
        for cat_id, category in self.categories.items():
            category.category_id = cat_id

        for category in self.categories.values():
            resolved_tags = []
            # Resolve tag references
            for tag_or_id in category.default_tags:
                if isinstance(tag_or_id, str):
                    tag_obj = self.tags.get(tag_or_id)
                    if not tag_obj:
                        raise ValueError(f"Couldn't find tag of id {tag_or_id}")
                    resolved_tags.append(tag_obj)
                    continue

                resolved_tags.append(tag_or_id)
            
            category.default_tags = resolved_tags
            # Resolve super category references
            if isinstance(category.super_category, str):
                super_cat_obj = self.categories.get(category.super_category)
                if not super_cat_obj:
                    raise ValueError(f"Couldn't find super category: {category.super_category} from {category.category_id} in header")
                category.super_category = super_cat_obj

        return self

class Metadata(MetadataFileHeader):
    data_types: dict[str, DataTypeMeta]
    node_types: dict[str, NodeTypeMeta]
    
    @field_serializer("data_types")
    def serialize_data_types(self, data_types: dict[str, DataTypeMeta], _info):
        return [id for id in data_types]

    @field_serializer("node_types")
    def serialize_node_types(self, node_types: dict[str, NodeTypeMeta], _info):
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

    def save_on_metadata(self):
        if not self.metadata:
            raise Exception("No metadata to save")
        
        meta_path = os.path.join(ROOT_METADATA_PATH, self.metadata.types_id)
        if not os.path.exists(meta_path): os.mkdir(meta_path)
        MetadataFile._save_to_folder(self.metadata, meta_path)

    def load_from_metadata(self, types_id: str):
        meta_path = os.path.join(ROOT_METADATA_PATH, types_id)
        self.metadata = MetadataFile._load_from_folder(meta_path)
        

    def set_from_types(self, type_reader: TypeFileReader):
        self.metadata = MetadataFile.generate_meta_model(type_reader)
    

    @staticmethod
    def generate_meta_model(type_reader: TypeFileReader) -> Metadata:
        if not type_reader._node_types_id: 
            raise Exception(f"TypeFile is missing node type id. Referred reader: {type_reader}")
        
        node_categories: dict[str, NodeCategory] = {}
        node_tags: dict[str, NodeTag] = {}
        for type_id, constructor in type_reader.node_constructors.items():
            category = constructor._metadata.category
            if isinstance(category, str): continue

            node_categories[category.category_id] = category 
            for tag in (constructor._metadata.tags + category.default_tags):
                if isinstance(tag, str): continue

                node_tags[tag.tag_id] = tag
        
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
            if not constructor._metadata.slot_meta:
                slot_meta: dict[str, SlotMeta] = {}
                for slot_id in constructor._slots:
                    slot_meta[slot_id] = SlotMeta(
                        capitalized_name=slot_id
                    )
                
                constructor._metadata.slot_meta.update(slot_meta)

            if not constructor._metadata.parameter_meta:
                param_meta: dict[str, ParameterMeta] = {}
                for param_name in constructor._data_model.param_model:
                    param_meta[param_name] = ParameterMeta(
                        capitalized_name=param_name
                    )
                constructor._metadata.parameter_meta.update(param_meta)
            
            meta = NodeTypeMeta(
                capitalized_name=constructor._metadata.capitalized_name,
                description=constructor._metadata.description,
                category=constructor._metadata.category,
                tags=constructor._metadata.tags,
                slot_meta=constructor._metadata.slot_meta,
                parameter_meta=constructor._metadata.parameter_meta
            )
            nodetype_meta[type_id] = meta
        
        metadata = Metadata(
            types_id=type_reader._node_types_id,
            meta_version=0,
            data_types=datatype_meta,
            node_types=nodetype_meta,
            tags=node_tags,
            categories=node_categories
        )
        return metadata

    @staticmethod
    def _save_to_folder(metadata: Metadata, folder_path: str):
        # TODO: load metadata from folder and compare each field so it doesn't override fields that were modified
        if not metadata:
            raise Exception("No metadata to save")
        
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
    
        if not os.path.isdir(folder_path):
            raise Exception("Folder path should lead to a folder")

        node_meta_path = os.path.join(folder_path, "nodes")
        datatypes_path = os.path.join(folder_path, "datatypes")
        if not os.path.exists(node_meta_path): os.mkdir(node_meta_path)
        if not os.path.exists(datatypes_path): os.mkdir(datatypes_path)
        
        for type_id, node_meta in metadata.node_types.items():
            # TODO: Ensure type id doesn't contain any special characters
            file_path = os.path.join(node_meta_path, f"{type_id}{METADATA_EXTENSION}")
            with open(file_path, "w") as file:
                file.write(node_meta.model_dump_json(indent=METADATA_INDENT))
        
        slotio_types = MetadataFile.get_slotio_subtypes(metadata.data_types)    
        for slotio_type, subtypes in slotio_types.items():
            slotio_folder_path = os.path.join(datatypes_path, slotio_type)
            if not os.path.isdir(slotio_folder_path): os.mkdir(slotio_folder_path)
            if len(subtypes) == 0: subtypes.append("default")
            for subtype in subtypes:
                type_id = MetadataFile.make_slotio_id_filename(slotio_type, subtype)
                subtype_file_path = os.path.join(slotio_folder_path, f"{subtype}{METADATA_EXTENSION}")
                subtype_meta = metadata.data_types.get(type_id)
                if not subtype_meta: 
                    raise Exception(f"Failed to find corresponding metadata for datatype {type_id}")
                
                with open(subtype_file_path, "w") as file:
                    file.write(subtype_meta.model_dump_json(indent=METADATA_INDENT))                
        
        header_file_path = os.path.join(folder_path, f"metadata{METADATA_EXTENSION}")
        with open(header_file_path, "w") as file:
            file.write(metadata.model_dump_json(indent=METADATA_INDENT))
    
    @staticmethod
    def _load_from_folder(folder_path: str):
        if not os.path.isdir(folder_path):
            raise Exception(f"Couldn't load metadata, folder path should lead to a folder. Path: {folder_path}")

        header_file_path = os.path.join(folder_path, f"metadata{METADATA_EXTENSION}")
        with open(header_file_path, "r") as file:
            header_data = json.load(file)
        
        header_metadata = MetadataFileHeader.model_validate(header_data)
        if not header_metadata:
            raise Exception(f"Couldn't parse metadata header. Path: {header_file_path}")

        node_types: dict[str, NodeTypeMeta] = {}
        node_meta_path = os.path.join(folder_path, "nodes")
        header_context = {
            "tags": header_metadata.tags,
            "categories": header_metadata.categories
        }
        if os.path.exists(node_meta_path):
            node_meta_files: list[str] = os.listdir(node_meta_path)
            for meta_filename in node_meta_files:
                meta_path = os.path.join(node_meta_path, meta_filename)
                if not os.path.isfile(meta_path): continue

                # FIXME: use file path to get type id might not be safe
                type_id = os.path.splitext(meta_filename)[0]
                with open(meta_path, "r") as file:
                    node_json_data = json.load(file)
                
                node_types[type_id] = NodeTypeMeta.model_validate(node_json_data, context=header_context)

        datatypes: dict[str, DataTypeMeta] = {}
        datatypes_path = os.path.join(folder_path, "datatypes")
        if os.path.exists(datatypes_path):
            datatype_files: list[str] = os.listdir(datatypes_path)
            for slotio_name in datatype_files:
                datatype_folder = os.path.join(datatypes_path, slotio_name)
                if not os.path.isdir(datatype_folder): continue
                
                for subtype_filename in os.listdir(datatype_folder):
                    subtype_path = os.path.join(datatype_folder, subtype_filename)
                    if not os.path.isfile(subtype_path): continue

                    subtype_name = os.path.splitext(subtype_filename)[0]
                    datatype_id = MetadataFile.make_slotio_id_filename(slotio_name, subtype_name)
                    with open(subtype_path, "r") as file:
                        datatype_data = json.load(file)
                    
                    datatypes[datatype_id] = DataTypeMeta.model_validate(datatype_data)
        
        return Metadata(
            types_id=header_metadata.types_id,
            meta_version=header_metadata.meta_version,
            tags=header_metadata.tags,
            categories=header_metadata.categories,
            data_types=datatypes,
            node_types=node_types
        )

    @staticmethod
    def make_slotio_id_filename(slotio_type: str, subtype: str):
        return f"{slotio_type}:{subtype}"
    
    @staticmethod
    def get_slotio_subtypes(data_types: dict[str, DataTypeMeta]):
        slotio_types: dict[str, list[str]] = {}
        for type_id in data_types:
            # TODO: Ensure type id doesn't contain any special characters
            splitted_type_id = type_id.split(":")
            slotio_type = splitted_type_id[0]
            if not slotio_types.__contains__(slotio_type):
                slotio_types[slotio_type] = []
            
            slotio_types[slotio_type] += splitted_type_id[1:] or []
    
        return slotio_types