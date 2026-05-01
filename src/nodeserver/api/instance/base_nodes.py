
import json
import os
import pathlib
from typing import Any, Optional

from nodeserver.api.internal.instance_state import InternalNodeState
from nodeserver.wrapper.nodes.data.node_data_types import SuperSlotTypes
from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror, SlotMirror, SlotOutput

# TODO: Change node inputs to a NodeOutput class or NodeInputs class
class BaseNode:
    _version: int = 0
    _mirror: NodeMirror

    dirty: bool = True
    bypass_cache: bool = False

    def __init__(self, mirror: NodeMirror | None = None):
        if mirror != None:
            self._mirror = mirror

    def pre_forward(self, input: dict[SlotMirror, dict[SlotMirror, SlotOutput]]):
        pass

    # TODO: Add a safety check before the actual forward
    # so the end developer can set what it needs as inputs
    # and just program what it does with the inputs (not to all the checks if the inputs exist)
    def forward(self, input: dict[SlotMirror, dict[SlotMirror, SlotOutput]]) -> dict[SlotMirror, SlotOutput]:
        output_data = {}
        return self.map_to_slots(output_data)
    
    def post_forward(self):
        pass


    def map_to_slots(self, data: dict[str, Any]) -> dict[SlotMirror, SlotOutput]:
        output_map: dict[SlotMirror, SlotOutput] = {}
        for key in data:
            slot = self._mirror.get_slot(key)
            if not slot:
                # ERROR
                continue
            
            if slot.type._super_type != SuperSlotTypes.OUTPUT:
                # ERROR
                continue
            
            slot._output.value = data[key]
            if self.bypass_cache:
                slot._output._version += 1

            output_map[slot] = slot._output

        return output_map

    # Override these on your Node class:
    # Your load state logic
    def load_state(self, root_state_path: str, state: InternalNodeState):
        if state.relative_state_path:
            my_state_file_path = os.path.join(root_state_path, state.relative_state_path)
            print(my_state_file_path)
            # Open file and load stuff


    # Should have save logic
    def save_state(self, root_state_path: str) -> Optional[InternalNodeState]:
        state = self.get_state()
        if state:
            my_state_file_path, filename = self.make_state_file_path(root_state_path, "json")
            state.relative_state_path = str(pathlib.Path(my_state_file_path).relative_to(root_state_path))
            
            with open(my_state_file_path, "w") as file:
                file.write(json.dumps({"some": "data"}))

        # Do some Save stuff if you need to
        return state

    # Shouldn't have save logic
    def get_state(self) -> Optional[InternalNodeState]:
        return InternalNodeState(
            relative_state_path=None,
            state_data=None
        )

    # Extension without .
    def make_state_file_path(self, root_path: str, extension: str) -> tuple[str, str]:
        filename = f"{self._mirror.uid}.{extension}"
        return os.path.join(root_path, filename), filename