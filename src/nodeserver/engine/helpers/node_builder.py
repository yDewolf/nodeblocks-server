from types import NoneType
from typing import Any, Optional, Union
import typing

from nodeserver.engine.helpers.logic_node_helper import LogicNodeHelper
from nodeserver.engine.protocols.node.logic_nodes import BaseNode, NodeIO
from nodeserver.engine.protocols.node.node_instance import NodeInstance, SlotInstance
from nodeserver.engine.protocols.spec_dataclasses import SlotSpecMeta
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.helpers.uuid_utils import IDGenerator
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData
from nodeserver.protocols.manifest.node.node_manifest import NodeSlotSpec, NodeTypeSpec

class NodeBuilder:
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
        slot_specs = LogicNodeHelper._generate_specs_for_slots(model_cls, is_input)
        slots: dict[str, SlotInstance] = {}
        
        for slot_id, spec in slot_specs.items():
            slots[slot_id] = SlotInstance(
                node_id=node_uid,
                slot_id=slot_id,
                spec=spec
            )
        
        return slots

   