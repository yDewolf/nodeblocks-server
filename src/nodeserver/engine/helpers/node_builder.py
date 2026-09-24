from types import NoneType
from typing import Any, Optional, Union
import typing

from nodeserver.engine.protocols.logic_nodes import BaseNode, NodeIO
from nodeserver.engine.protocols.node_instance import NodeInstance, SlotInstance
from nodeserver.engine.protocols.slot_spec_meta import SlotSpecMeta
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.helpers.uuid_utils import IDGenerator
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData
from nodeserver.protocols.manifest.node.node_manifest import NodeSlotSpec, NodeTypeSpec

class NodeBuilder:
    TYPE_MAP = {
        int: "core:int",
        float: "core:float",
        str: "core:string",
        bool: "core:bool",
    }
    
    @staticmethod
    def build(type_spec: NodeTypeSpec, type_registry: TypeRegistry, node_scene_data: Optional[NodeSceneData]) -> tuple[NodeInstance, BaseNode]:
        node_scene_data = node_scene_data or NodeSceneData(uid=IDGenerator.generate_node_id(), type_id=type_spec.fqn)
        if node_scene_data.data == {}:
            node_scene_data.data = {
                key: param_spec.default for key, param_spec in type_spec.parameters.items()
            }
        
        logic_instance = type_registry.get_logic_class(type_spec.fqn)(node_scene_data) 
        
        slots: dict[str, SlotInstance] = {
            **NodeBuilder._create_slots_from_model(logic_instance.InputModel, node_scene_data.uid, True),
            **NodeBuilder._create_slots_from_model(logic_instance.OutputModel, node_scene_data.uid, False),
        }

        return (NodeInstance(
            uid=node_scene_data.uid,
            scene_data=node_scene_data,
            slots=slots
        ), logic_instance)

    @staticmethod
    def _create_slots_from_model(
        model_cls: type[NodeIO], 
        node_uid: str, 
        is_input: bool
    ) -> dict[str, SlotInstance]:
        slots: dict[str, SlotInstance] = {}
        
        for field_name, field_info in model_cls.model_fields.items():
            meta, is_default = NodeBuilder._extract_slot_meta(field_info)

            datatype = meta.datatype if not is_default else NodeBuilder._infer_datatype_from_type(field_info.annotation)

            is_collection = typing.get_origin(field_info.annotation) is list
            max_connections: int = (
                meta.max_connections if meta.max_connections is not None 
                else (0 if (is_collection or not is_input) else 1)
            )

            # TODO:
           
            slots[field_name] = SlotInstance(
                slot_id=field_name,
                node_id=node_uid,
                spec=NodeSlotSpec(
                    is_input=is_input,
                    data_type_id=datatype.id if isinstance(datatype, DataTypeSpec) else datatype,
                    max_connections=max_connections
                )
            )
            
        return slots

    @staticmethod
    def _infer_datatype_from_type(annotation: Any) -> str:
        origin = typing.get_origin(annotation)
        
        if origin is list:
            args = typing.get_args(annotation)
            annotation = args[0] if args else Any
        
        # Se for Optional[T] / Union[T, None], extrai T
        elif origin is Union:
            args = [arg for arg in typing.get_args(annotation) if arg is not NoneType]
            if args: annotation = args[0]

        return NodeBuilder.TYPE_MAP.get(annotation, "core:unknown") # FIXME: substituir o fqn por enum value

    @staticmethod
    def _extract_slot_meta(field_info) -> tuple[SlotSpecMeta, bool]:
        for meta in getattr(field_info, "metadata", []):
            if isinstance(meta, SlotSpecMeta):
                return meta, False
                
        return SlotSpecMeta("core:unknown"), True # FIXME: substituir o fqn por enum value
