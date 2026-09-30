from __future__ import annotations
from typing import Optional

from nodeserver.protocols.manifest.node.node_graph import NodeSceneData
from nodeserver.protocols.manifest.node.node_manifest import NodeSlotSpec

class SlotInstance:
    node_id: str
    slot_id: str   
    spec: NodeSlotSpec

    def __init__(self, node_id: str, slot_id: str, spec: NodeSlotSpec) -> None:
        self.node_id = node_id
        self.slot_id = slot_id
        self.spec = spec
        
        self.connection_count: int = 0 # updated by SceneGraph

    @property
    def is_input(self) -> bool:
        return self.spec.is_input

    @property
    def can_connect(self) -> bool:
        return self.spec.max_connections == 0 or self.connection_count < self.spec.max_connections 

    @property
    def data_type_id(self) -> str:
        return self.spec.data_type_id


class NodeInstance:
    node_data: NodeSceneData
    slots: dict[str, SlotInstance]

    # TODO: implementar os NodeParameters com typesafety !!
    def __init__(self, scene_data: NodeSceneData, uid: Optional[str] = None, slots: dict[str, SlotInstance] = {}):
        self.node_data = scene_data
        if uid: self.node_data.uid = uid

        self.slots = slots

    @property
    def uid(self): return self.node_data.uid

    @property
    def type_id(self): return self.node_data.type_id


    def add_slot(self, slot_id: str, spec: NodeSlotSpec) -> SlotInstance:
        slot = SlotInstance(node_id=self.uid, slot_id=slot_id, spec=spec)
        self.slots[slot_id] = slot
        return slot

    def get_slot(self, slot_id: str) -> SlotInstance | None:
        return self.slots.get(slot_id)

