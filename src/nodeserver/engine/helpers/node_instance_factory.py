from typing import Optional

from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.engine.protocols.node.node_instance import NodeInstance, SlotInstance
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.helpers.uuid_utils import IDGenerator
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData
from nodeserver.protocols.manifest.node.node_manifest import NodeTypeSpec


class NodeInstanceFactory:
    def __init__(self, registry: TypeRegistry):
        self.registry = registry

    def create(
        self, 
        node_fqn: str, 
        node_scene_data: Optional[NodeSceneData] = None
    ) -> tuple[NodeInstance, BaseNode]:
        spec = self.registry.get_node_spec(node_fqn)
        if not spec: raise ValueError(f"Unknown node type: {node_fqn}")

        node_scene_data = node_scene_data or NodeSceneData(
            uid=IDGenerator.generate_node_id(), 
            type_id=spec.fqn
        )

        if not node_scene_data.data:
            node_scene_data.data = {
                key: param_spec.default for key, param_spec in spec.parameters.items()
            }

        logic_class = self.registry.get_logic_class(spec.fqn)
        logic_instance = logic_class(node_scene_data)

        slots = self._create_slots_from_spec(spec, node_scene_data.uid)

        node_instance = NodeInstance(
            uid=node_scene_data.uid,
            scene_data=node_scene_data,
            slots=slots
        )

        return node_instance, logic_instance

    def _create_slots_from_spec(self, spec: NodeTypeSpec, node_uid: str) -> dict[str, SlotInstance]:
        slots: dict[str, SlotInstance] = {}

        for slot_id, slot_spec in spec.slots.items():
            slots[slot_id] = SlotInstance(
                node_id=node_uid,
                slot_id=slot_id,
                spec=slot_spec
            )

        return slots
