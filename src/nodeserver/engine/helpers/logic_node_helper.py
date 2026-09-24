from types import NoneType
from typing import Any, Union, get_args, get_origin

from nodeserver.engine.protocols.node.logic_nodes import NodeIO
from nodeserver.engine.protocols.spec_dataclasses import SlotSpecMeta
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec
from nodeserver.protocols.manifest.node.node_manifest import NodeSlotSpec


class LogicNodeHelper:
    TYPE_MAP = {
        int: "core:int",
        float: "core:float",
        str: "core:string",
        bool: "core:bool",
    } # TODO: get these values from core plugin 
    
    @staticmethod
    def _infer_datatype_from_type(annotation: Any) -> str:
        origin = get_origin(annotation)
        
        if origin is list:
            args = get_args(annotation)
            annotation = args[0] if args else Any
        
        # Se for Optional[T] / Union[T, None], extrai T
        elif origin is Union:
            args = [arg for arg in get_args(annotation) if arg is not NoneType]
            if args: annotation = args[0]

        return LogicNodeHelper.TYPE_MAP.get(annotation, "core:unknown") # FIXME: substituir o fqn por enum value


    @staticmethod
    def _extract_slot_meta(field_info) -> tuple[SlotSpecMeta, bool]:
        for meta in getattr(field_info, "metadata", []):
            if isinstance(meta, SlotSpecMeta):
                return meta, False
                
        return SlotSpecMeta("core:unknown"), True # FIXME: substituir o fqn por enum value


    # Utility method to generate specs using a NodeIO class (BaseModel)
    
    @staticmethod
    def _generate_specs_for_slots(slot_model_cls: type[NodeIO], is_input: bool) -> dict[str, NodeSlotSpec]:
        slot_specs: dict[str, NodeSlotSpec] = {}
        for field_name, field_info in slot_model_cls.model_fields.items():
            meta, is_default = LogicNodeHelper._extract_slot_meta(field_info)
            datatype = meta.datatype if not is_default else LogicNodeHelper._infer_datatype_from_type(field_info.annotation)

            is_collection = get_origin(field_info.annotation) is list
            max_connections: int = (
                meta.max_connections if meta.max_connections is not None 
                else (0 if (is_collection or not is_input) else 1)
            )

            slot_specs[field_name] = NodeSlotSpec(
                is_input=is_input,
                data_type_id=datatype.id if isinstance(datatype, DataTypeSpec) else datatype,
                max_connections=max_connections,
                required=meta.required,
            )
            
        return slot_specs
