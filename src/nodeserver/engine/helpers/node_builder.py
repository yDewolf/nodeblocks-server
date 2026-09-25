from types import NoneType
from typing import Any, Optional, Union
import typing

from nodeserver.engine.helpers.node_spec_builder import NodeSpecBuilder
from nodeserver.engine.protocols.node.logic_nodes import BaseNode, NodeIO
from nodeserver.engine.protocols.node.node_instance import NodeInstance, SlotInstance
from nodeserver.engine.protocols.spec_dataclasses import SlotSpecMeta
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.helpers.uuid_utils import IDGenerator
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData
from nodeserver.protocols.manifest.node.node_manifest import NodeSlotSpec, NodeTypeSpec

class NodeBuilder:
    registry: TypeRegistry
    spec_builder: NodeSpecBuilder
    
    def __init__(self, registry: TypeRegistry, spec_builder: Optional[NodeSpecBuilder] = None) -> None:
        self.registry = registry
        self.spec_builder = spec_builder or NodeSpecBuilder(registry)

    def build_instance(self, type_spec: NodeTypeSpec, node_scene_data: Optional[NodeSceneData]) -> tuple[NodeInstance, BaseNode]:
        node_scene_data = node_scene_data or NodeSceneData(uid=IDGenerator.generate_node_id(), type_id=type_spec.fqn)
        if node_scene_data.data == {}:
            node_scene_data.data = {
                key: param_spec.default for key, param_spec in type_spec.parameters.items()
            }
        
        logic_instance = self.registry.get_logic_class(type_spec.fqn)(node_scene_data) 
        slots: dict[str, SlotInstance] = {
            **self._create_slots_from_model(logic_instance.InputModel, node_scene_data.uid, True),
            **self._create_slots_from_model(logic_instance.OutputModel, node_scene_data.uid, False),
        }

        return (NodeInstance(
            uid=node_scene_data.uid,
            scene_data=node_scene_data,
            slots=slots
        ), logic_instance)

    def _create_slots_from_model(
        self,
        model_cls: type[NodeIO], 
        node_uid: str, 
        is_input: bool
    ) -> dict[str, SlotInstance]:
        slot_specs = self.spec_builder._generate_specs_for_slots(model_cls, is_input)
        slots: dict[str, SlotInstance] = {}
        
        for slot_id, spec in slot_specs.items():
            slots[slot_id] = SlotInstance(
                node_id=node_uid,
                slot_id=slot_id,
                spec=spec
            )
        
        return slots

   