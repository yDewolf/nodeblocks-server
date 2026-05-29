import os
from typing import Optional

from nodeserver.wrapper.metadata.helpers.metadata_utils import METADATA_EXTENSION, ROOT_METADATA_PATH, MetadataFileUtils
from nodeserver.wrapper.metadata.metadata_header import Metadata
from nodeserver.wrapper.metadata.nodes.datatype_metadata import DataTypeMeta
from nodeserver.wrapper.metadata.nodes.node_metadata import NodeCategory, NodeTag, NodeTypeMeta, ParameterMeta, SlotMeta
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import TypeFileReader


class MetadataFile:
    metadata: Optional[Metadata] = None
    last_update_timestamp: float = 0.0

    def __init__(self) -> None:
        pass

    @classmethod
    def new(cls, type_reader: TypeFileReader, fetch_from_disk: bool = False) -> "MetadataFile":
        """
            Creates a :obj:`MetadataFile` object using ``type_reader`` default metadata 
            as reference. 
            
            See Also:
                :meth:`~nodeserver.MetadataFile.set_from_types`
                :meth:`~nodeserver.MetadataFile.generate_meta_model`
        """
        metadata_file = MetadataFile()
        metadata_file.set_from_types(type_reader)
        if fetch_from_disk:
            metadata_file.save_on_metadata()
            metadata_file.reload_from_disk()

        return metadata_file


    def has_modifications_on_disk(self) -> bool:
        if not self.metadata:
            return False
        
        if self.last_update_timestamp < self.get_global_mtime():
            return True

        return False

    def reload_from_disk(self, only_if_modified: bool = False) -> bool:
        if only_if_modified:
            if not self.has_modifications_on_disk():
                return False
        
        if not self.metadata:
            raise Exception("No metadata was loaded so it can't reload from disk")
        
        self.load_from_metadata(self.metadata.types_id)
        return True


    def save_on_metadata(self):
        """
            Saves metadata content from this object in ``{ROOT_METADATA_PATH}/{self.metadata.types_id}``.

            See also:
                :meth:`~nodeserver.MetadataFileUtils`
                :meth:`~nodeserver.MetadataFileUtils.save_to_folder`
        """
        if not self.metadata:
            raise Exception("No metadata to save")
        
        meta_path = os.path.join(ROOT_METADATA_PATH, self.metadata.types_id)
        if not os.path.exists(meta_path): os.mkdir(meta_path)
        MetadataFileUtils.save_to_folder(self.metadata, meta_path)

    def load_from_metadata(self, types_id: str):
        """
            Loads metadata from ``{ROOT_METADATA_PATH}/{self.metadata.types_id}``.

            See also:
                :obj:`~nodeserver.MetadataFileUtils`
                :meth:`~nodeserver.MetadataFileUtils.load_from_folder`
        """
        meta_path = os.path.join(ROOT_METADATA_PATH, types_id)
        self.metadata = MetadataFileUtils.load_from_folder(meta_path)
        MetadataFileUtils.update_content_hash(self.metadata, meta_path)
        if self.metadata.last_modified:
            self.last_update_timestamp = self.metadata.last_modified

    def get_global_mtime(self):
        if not self.metadata:
            return self.last_update_timestamp
        
        return MetadataFileUtils.get_global_mtime(self.metadata)


    def set_from_types(self, type_reader: TypeFileReader):
        self.metadata = MetadataFile.generate_meta_model(type_reader)    

    @staticmethod
    def generate_meta_model(type_reader: TypeFileReader) -> Metadata:
        if not type_reader._node_types_id: 
            raise Exception(f"TypeFile is missing node type id. Referred reader: {type_reader}")
        
        node_categories: dict[str, NodeCategory] = {}
        node_tags: dict[str, NodeTag] = {}
        for type_id, constructor in type_reader.node_constructors.items():
            category = constructor._base_metadata.category
            if isinstance(category, str): continue

            node_categories[category.category_id] = category 
            for tag in (constructor._base_metadata.tags + category.default_tags):
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
            if not constructor._base_metadata.slot_meta:
                slot_meta: dict[str, SlotMeta] = {}
                for slot_id in constructor._slots:
                    slot_meta[slot_id] = SlotMeta(
                        capitalized_name=slot_id
                    )
                
                constructor._base_metadata.slot_meta.update(slot_meta)

            if not constructor._base_metadata.parameter_meta:
                param_meta: dict[str, ParameterMeta] = {}
                for param_id, param_data in constructor._data_model.param_model.items():
                    param_meta[param_id] = ParameterMeta(
                        capitalized_name=param_data.label if param_data.label else param_id
                    )
                constructor._base_metadata.parameter_meta.update(param_meta)
            
            meta = NodeTypeMeta(
                capitalized_name=constructor._base_metadata.capitalized_name,
                description=constructor._base_metadata.description,
                category=constructor._base_metadata.category,
                tags=constructor._base_metadata.tags,
                slot_meta=constructor._base_metadata.slot_meta,
                parameter_meta=constructor._base_metadata.parameter_meta
            )
            nodetype_meta[type_id] = meta
        
        metadata = Metadata(
            types_id=type_reader._node_types_id,
            types_version=type_reader._node_types_version,
            last_modified=None,
            meta_version=0,
            data_types=datatype_meta,
            node_types=nodetype_meta,
            tags=node_tags,
            categories=node_categories
        )
        return metadata
