
from typing import Any

from nodeserver.wrapper.nodes.data.node_data_types import SuperSlotTypes
from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror, SlotMirror


# TODO: Change node inputs to a NodeOutput class or NodeInputs class
class BaseNode:
    _mirror: NodeMirror
    def __init__(self, mirror: NodeMirror | None = None):
        if mirror != None:
            self._mirror = mirror

    # TODO: Add a safety check before the actual forward
    # so the end developer can set what it needs as inputs
    # and just program what it does with the inputs (not to all the checks if the inputs exist)
    def forward(self, inputs: dict[SlotMirror, dict[SlotMirror, dict]]) -> dict[SlotMirror, Any]:
        output_data = {}
        return self.map_to_slots(output_data)
    
    def map_to_slots(self, data: dict[str, Any]) -> dict[SlotMirror, Any]:
        output_map: dict[SlotMirror, Any] = {}
        for key in data:
            slot = self._mirror.get_slot(key)
            if not slot:
                # ERROR
                continue
            
            if slot.type._super_type != SuperSlotTypes.OUTPUT:
                # ERROR
                continue
            
            output_map[slot] = data[key]

        return output_map