import json
import os

from nodeserver.api.utils.file_utils import get_project_root
from nodeserver.wrapper.metadata.metadata_header import Metadata, MetadataFileHeader
from nodeserver.wrapper.metadata.nodes.datatype_metadata import DataTypeMeta
from nodeserver.wrapper.metadata.nodes.node_metadata import NodeTypeMeta
import logging
logger = logging.getLogger("nds.metadata")

METADATA_EXTENSION = ".json"
METADATA_INDENT = 1

ROOT_METADATA_PATH = os.path.join(get_project_root(), "metadata")

"""
    General Metadata Folder Structure:
    types_id/
        metadata.json (header file)
        datatypes/
            SlotIOType/
                subtype.json
                default.json (if no subtype is found)
        nodes/
            NodeTypeID.json
"""
class _MetadataLoad:
    @staticmethod
    def _load_header(folder_path: str) -> MetadataFileHeader:
        header_file_path = os.path.join(folder_path, f"metadata{METADATA_EXTENSION}")
        with open(header_file_path, "r") as file:
            header_data = json.load(file)
        
        header_metadata = MetadataFileHeader.model_validate(header_data)
        if not header_metadata:
            raise Exception(f"Couldn't parse metadata header. Path: {header_file_path}")

        return header_metadata

    @staticmethod
    def _load_node_types(header: MetadataFileHeader, folder_path: str) -> dict[str, NodeTypeMeta]:
        header_context = {
            "tags": header.tags,
            "categories": header.categories
        }

        node_types: dict[str, NodeTypeMeta] = {}
        node_meta_path = os.path.join(folder_path, "nodes")
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

        return node_types

    @staticmethod
    def _load_data_types(folder_path: str) -> dict[str, DataTypeMeta]:
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
                    datatype_id = MetadataFileUtils.make_slotio_id_filename(slotio_name, subtype_name)
                    with open(subtype_path, "r") as file:
                        datatype_data = json.load(file)
                    
                    datatypes[datatype_id] = DataTypeMeta.model_validate(datatype_data)
        
        return datatypes

class _MetadataSave:
    @staticmethod
    def _deep_merge(base: dict, overrides: dict) -> dict:
        """
            Recursively merges dicts ``base`` and ``overrides``
            ``overrides`` (should come from disk) has priority over ``base`` (should come from default metadata)
            New fields from ``base`` that doesn't exist in ``overrides`` will be preserved.
        """
        merged = base.copy()
        for key, value in overrides.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                merged[key] = _MetadataSave._deep_merge(merged[key], value)
                continue
            merged[key] = value

        return merged

    @staticmethod
    def _prepare_directories(folder_path: str) -> tuple[str, str]:
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
    
        if not os.path.isdir(folder_path):
            raise Exception("Folder path should lead to a folder")

        node_meta_path = os.path.join(folder_path, "nodes")
        datatypes_path = os.path.join(folder_path, "datatypes")
        if not os.path.exists(node_meta_path): os.mkdir(node_meta_path)
        if not os.path.exists(datatypes_path): os.mkdir(datatypes_path)

        return node_meta_path, datatypes_path

    @staticmethod
    def _write_node_types(metadata: Metadata, node_meta_path: str):
        header_context = {
            "tags": metadata.tags,
            "categories": metadata.categories
        }
        for type_id, node_meta in metadata.node_types.items():
            # TODO: Ensure type id doesn't contain any special characters
            file_path = os.path.join(node_meta_path, f"{type_id}{METADATA_EXTENSION}")

            base_data = node_meta.model_dump(mode="json")
            merged_data = base_data
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r") as file:
                        disk_data = json.load(file)
                    merged_data = _MetadataSave._deep_merge(base_data, disk_data)
                except Exception as e:
                    logger.error("Failed to load node metadata.", e)

            merged_model = NodeTypeMeta.model_validate(merged_data, context=header_context)
            with open(file_path, "w") as file:
                file.write(merged_model.model_dump_json(indent=METADATA_INDENT))

    @staticmethod
    def _write_datatypes(metadata: Metadata, datatypes_path: str):
        slotio_types = MetadataFileUtils.get_slotio_subtypes(metadata.data_types)    
        for slotio_type, subtypes in slotio_types.items():
            slotio_folder_path = os.path.join(datatypes_path, slotio_type)
            if not os.path.isdir(slotio_folder_path): os.mkdir(slotio_folder_path)
            if len(subtypes) == 0: subtypes.append("default")
            for subtype in subtypes:
                type_id = MetadataFileUtils.make_slotio_id_filename(slotio_type, subtype)
                subtype_file_path = os.path.join(slotio_folder_path, f"{subtype}{METADATA_EXTENSION}")
                subtype_meta = metadata.data_types.get(type_id)
                if not subtype_meta: 
                    raise Exception(f"Failed to find corresponding metadata for datatype {type_id}")
                
                base_data = subtype_meta.model_dump(mode="json")
                merged_data = base_data
                if os.path.exists(subtype_file_path):
                    try:
                        with open(subtype_file_path, "r") as file:
                            disk_data = json.load(file)
                        merged_data = _MetadataSave._deep_merge(base_data, disk_data)
                    except Exception as e:
                        logger.error("Failed to load subtype metadata.", e)

                merged_model = DataTypeMeta.model_validate(merged_data)
                with open(subtype_file_path, "w") as file:
                    file.write(merged_model.model_dump_json(indent=METADATA_INDENT))    

    @staticmethod
    def _write_header(metadata: Metadata, folder_path: str):
        header_file_path = os.path.join(folder_path, f"metadata{METADATA_EXTENSION}")
        base_data = metadata.model_dump(mode="json")
        merged_data = base_data
        if os.path.exists(header_file_path):
            try:
                with open(header_file_path, "r") as file:
                    disk_data = json.load(file)
                merged_data = _MetadataSave._deep_merge(base_data, disk_data)
            except Exception as e:
                logger.error("Failed to load metadata header.", e)
            
        merged_model = MetadataFileHeader.model_validate(merged_data)
        with open(header_file_path, "w") as file:
            file.write(merged_model.model_dump_json(indent=METADATA_INDENT))
    

class MetadataFileUtils:
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

    
    @staticmethod
    def save_to_folder(metadata: Metadata, folder_path: str):
        if not metadata:
            raise Exception("No metadata to save")
        
        node_meta_path, datatypes_path = _MetadataSave._prepare_directories(folder_path)
        _MetadataSave._write_node_types(metadata, node_meta_path)
        _MetadataSave._write_datatypes(metadata, datatypes_path)
        _MetadataSave._write_header(metadata, folder_path)    

    @staticmethod
    def load_from_folder(folder_path: str):
        if not os.path.isdir(folder_path):
            raise Exception(f"Couldn't load metadata, folder path should lead to a folder. Path: {folder_path}")

        header_metadata = _MetadataLoad._load_header(folder_path)
        datatypes: dict[str, DataTypeMeta] = _MetadataLoad._load_data_types(folder_path)
        node_types: dict[str, NodeTypeMeta] = _MetadataLoad._load_node_types(header_metadata, folder_path)
        
        return Metadata(
            types_id=header_metadata.types_id,
            meta_version=header_metadata.meta_version,
            tags=header_metadata.tags,
            categories=header_metadata.categories,
            data_types=datatypes,
            node_types=node_types
        )