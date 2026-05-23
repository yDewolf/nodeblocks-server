import os
from typing import Optional

from nodeserver.wrapper.metadata.helpers.metadata_utils import ROOT_METADATA_PATH, MetadataFileUtils
from nodeserver.wrapper.metadata.metadata_header import Metadata
from nodeserver.wrapper.metadata.nodes.datatype_metadata import DataTypeMeta
from nodeserver.wrapper.metadata.nodes.node_metadata import NodeCategory, NodeTag, NodeTypeMeta, ParameterMeta, SlotMeta
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import TypeFileReader


class MetadataFile:
    metadata: Optional[Metadata] = None
    def __init__(self) -> None:
        pass

    @classmethod
    def new(cls, type_reader: TypeFileReader) -> "MetadataFile":
        metadata_file = MetadataFile()
        metadata_file.set_from_types(type_reader)
        return metadata_file

    def save_on_metadata(self, override: bool = False):
        if not self.metadata:
            raise Exception("No metadata to save")
        
        meta_path = os.path.join(ROOT_METADATA_PATH, self.metadata.types_id)
        if not os.path.exists(meta_path): os.mkdir(meta_path)
        MetadataFileUtils.save_to_folder(self.metadata, meta_path)

    def load_from_metadata(self, types_id: str):
        meta_path = os.path.join(ROOT_METADATA_PATH, types_id)
        self.metadata = MetadataFileUtils.load_from_folder(meta_path)
        

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
