import datetime
import hashlib
import json
import os
from pathlib import Path

# TODO: mover isso aqui para o server e reestruturar as coisas
# para isso aqui ser um MetadataProvider

from nodeserver.protocols.manifest.metadata.metadata_header import Metadata, MetadataFileHeader
from nodeserver.protocols.manifest.metadata.datatype_meta import DataTypeMeta
from nodeserver.protocols.manifest.metadata.node_meta import NodeTypeMeta
import logging
logger = logging.getLogger("nds.metadata")

METADATA_EXTENSION = ".json"
METADATA_INDENT = 1

METADATA_FOLDER_NAME = "metadata"

class _MetadataLoad:
    """
        Helper class for metadata loading.
        Please use :obj:`~nodeserver.MetadataFileUtils` if you only need to load full metadata.
    """
    @staticmethod
    def _load_header(folder_path: Path) -> MetadataFileHeader:
        header_file_path = folder_path / f"metadata{METADATA_EXTENSION}"
        with open(header_file_path, "r") as file:
            header_data = json.load(file)
        
        header_metadata = MetadataFileHeader.model_validate(header_data)
        if not header_metadata:
            raise Exception(f"Couldn't parse metadata header. Path: {header_file_path}")

        return header_metadata

    @staticmethod
    def _load_node_types(header: MetadataFileHeader, folder_path: Path) -> dict[str, NodeTypeMeta]:
        header_context = {
            "tags": header.tags,
            "categories": header.categories
        }

        node_types: dict[str, NodeTypeMeta] = {}
        node_meta_path = folder_path / "nodes"
        if not node_meta_path.exists():
            return node_types
        
        node_meta_files: list[str] = dir(node_meta_path)
        for meta_filename in node_meta_files:
            meta_path = node_meta_path / meta_filename
            if not meta_path.is_file(): continue

            with open(meta_path, "r", encoding="utf-8") as file:
                node_json_data = json.load(file)
            
            type_id = Path(meta_filename).stem
            node_types[type_id] = NodeTypeMeta.model_validate(node_json_data, context=header_context)

        return node_types

    @staticmethod
    def _load_data_types(folder_path: Path) -> dict[str, DataTypeMeta]:
        datatypes: dict[str, DataTypeMeta] = {}
        datatypes_path = folder_path / "datatypes"
        if not datatypes_path.exists():
            return datatypes

        datatype_files: list[str] = dir(datatypes_path)
        for filename in datatype_files:
            datatype_path = datatypes_path / filename
            if not datatype_path.is_file(): continue

            with open(datatype_path, "r", encoding="utf-8") as file:
                datatype_data = json.load(file)

            datatype_id = Path(filename).stem
            datatypes[datatype_id] = DataTypeMeta.model_validate(datatype_data)
        
        return datatypes

class _MetadataSave:
    """
        Helper class for metadata saving.
        Please use :obj:`~nodeserver.MetadataFileUtils` if you only need to save full metadata.
    """
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
    def _prepare_directories(folder_path: Path) -> tuple[Path, Path]:
        folder_path.mkdir(exist_ok=True)
        if not folder_path.is_dir():
            raise Exception("Folder path should lead to a folder")
        
        node_meta_path, datatypes_path = MetadataFileUtils.get_metadata_main_subdirs(folder_path)
        node_meta_path.mkdir(exist_ok=True)
        datatypes_path.mkdir(exist_ok=True)

        return node_meta_path, datatypes_path

    @staticmethod
    def _write_node_types(metadata: Metadata, node_meta_path: Path):
        header_context = {
            "tags": metadata.tags,
            "categories": metadata.categories
        }
        for type_id, node_meta in metadata.node_types.items():
            # TODO: Ensure type id doesn't contain any special characters
            file_path = node_meta_path / f"{type_id}{METADATA_EXTENSION}"

            base_data = node_meta.model_dump(mode="json")
            merged_data = base_data
            
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        disk_data = json.load(file)
                    merged_data = _MetadataSave._deep_merge(base_data, disk_data)
                
                except Exception as e:
                    logger.error("Failed to load node metadata.", e)

            merged_model = NodeTypeMeta.model_validate(merged_data, context=header_context)
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(merged_model.model_dump_json(indent=METADATA_INDENT))

    @staticmethod
    def _write_datatypes(metadata: Metadata, datatypes_path: Path):
        for id, datatype in metadata.data_types.items():
            slotio_folder_path = datatypes_path / id

            slotio_folder_path.mkdir(exist_ok=True)

            subtype_file_path = slotio_folder_path / f"{id}{METADATA_EXTENSION}"
            
            base_data = datatype.model_dump(mode="json")
            merged_data = base_data
            if subtype_file_path.exists():
                try:
                    with open(subtype_file_path, "r", encoding="utf-8") as file:
                        disk_data = json.load(file)
                    merged_data = _MetadataSave._deep_merge(base_data, disk_data)
                except Exception as e:
                    logger.error("Failed to load subtype metadata.", e)

            merged_model = DataTypeMeta.model_validate(merged_data)
            with open(subtype_file_path, "w", encoding="utf-8") as file:
                file.write(merged_model.model_dump_json(indent=METADATA_INDENT))    

    @staticmethod
    def _write_header(metadata: Metadata, folder_path: Path):
        header_file_path = folder_path / f"metadata{METADATA_EXTENSION}"
        base_data = metadata.model_dump(mode="json")
        merged_data = base_data
        if header_file_path.exists():
            try:
                with open(header_file_path, "r", encoding="utf-8") as file:
                    disk_data = json.load(file)
                merged_data = _MetadataSave._deep_merge(base_data, disk_data)
            except Exception as e:
                logger.error("Failed to load metadata header.", e)
        
        merged_model = MetadataFileHeader.model_validate(merged_data)
        merged_model.content_hash = metadata.content_hash
        merged_model.package_version = metadata.package_version
        merged_model.meta_version = metadata.meta_version
        merged_model.last_modified = metadata.last_modified

        with open(header_file_path, "w", encoding="utf-8") as file:
            file.write(merged_model.model_dump_json(indent=METADATA_INDENT))
    

class MetadataFileUtils:
    """
        General Metadata Folder Structure:

        - plugin_folder/
            - metadata/
                - metadata.json (header file)
                - datatypes/
                    - SlotIOType/
                        - subtype.json
                        - default.json (if no subtype is found)
                - nodes/
                    - NodeTypeID.json
    """
    @staticmethod
    def get_global_mtime(metadata: Metadata, metadata_folder_path: Path) -> float:
        if not metadata:
            return 0.0
        
        nodes_path, datatypes_path = MetadataFileUtils.get_metadata_main_subdirs(metadata_folder_path)
        header_file = os.path.join(metadata_folder_path, f"metadata{METADATA_EXTENSION}")
        highest_mtime = 0.0
        if os.path.exists(header_file):
            highest_mtime = max(highest_mtime, os.path.getmtime(header_file))

        subdatatype_paths: list[str] = []
        with os.scandir(datatypes_path) as entries:
            subdatatype_paths += [entry.path for entry in entries]

        directory_lookup = [nodes_path] + subdatatype_paths
        for path in directory_lookup:
            if not os.path.exists(path):
                continue

            with os.scandir(path) as entries:
                for entry in entries:
                    if entry.is_file() and entry.name.endswith(METADATA_EXTENSION):
                        highest_mtime = max(highest_mtime, entry.stat().st_mtime)

        date = datetime.datetime.fromtimestamp(highest_mtime)
        return highest_mtime

    @staticmethod
    def get_metadata_main_subdirs(folder_path: Path) -> tuple[Path, Path]:
        node_meta_path = folder_path / "nodes"
        datatypes_path = folder_path / "datatypes"
        return node_meta_path, datatypes_path

    @staticmethod
    def update_metadata_header(metadata: Metadata, folder_path: Path):
        if not metadata:
            raise Exception("No metadata to save")
        
        _MetadataSave._write_header(metadata, folder_path)
    
    @staticmethod
    def save_to_folder(metadata: Metadata, folder_path: Path):
        if not metadata:
            raise Exception("No metadata to save")
        
        node_meta_path, datatypes_path = _MetadataSave._prepare_directories(folder_path)
        _MetadataSave._write_node_types(metadata, node_meta_path)
        _MetadataSave._write_datatypes(metadata, datatypes_path)
        _MetadataSave._write_header(metadata, folder_path)

    @staticmethod
    def load_from_folder(folder_path: Path):
        if not os.path.isdir(folder_path):
            raise Exception(f"Couldn't load metadata, folder path should lead to a folder. Path: {folder_path}")

        header_metadata = _MetadataLoad._load_header(folder_path)
        datatypes: dict[str, DataTypeMeta] = _MetadataLoad._load_data_types(folder_path)
        node_types: dict[str, NodeTypeMeta] = _MetadataLoad._load_node_types(header_metadata, folder_path)
        
        metadata = Metadata(
            content_hash=header_metadata.content_hash,
            package_id=header_metadata.package_id,
            package_version=header_metadata.package_version,
            meta_version=header_metadata.meta_version,
            last_modified=header_metadata.last_modified,
            tags=header_metadata.tags,
            categories=header_metadata.categories,
            data_types=datatypes,
            node_types=node_types
        )
        return metadata
    
    @staticmethod
    def update_content_hash(metadata: Metadata, metadata_folder_path: Path) -> bool:
        header_content = metadata.model_dump(mode="json", exclude={"meta_version", "content_hash", "last_modified"})
        metadata_content = {
            "header": header_content,
            "datatypes": {id: datatype.model_dump(mode="json") for id, datatype in metadata.data_types.items()},
            "node_types": {id: node_type.model_dump(mode="json") for id, node_type in metadata.node_types.items()}
        }
        current_hash = hashlib.md5(json.dumps(metadata_content).encode('utf-8')).hexdigest()
        saved_hash = metadata.content_hash
        if current_hash != saved_hash:
            metadata.last_modified = MetadataFileUtils.get_global_mtime(metadata, metadata_folder_path)
            metadata.meta_version += 1
            metadata.content_hash = current_hash
            _MetadataSave._write_header(metadata, metadata_folder_path)
            return True
        
        return False
