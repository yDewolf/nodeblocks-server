
from abc import abstractmethod
import json
import os
import pathlib
from typing import Any, Optional, Type, get_args, get_origin, get_type_hints

from pydantic import BaseModel, typing

from nodeserver.api.internal.instance_state import InternalNodeState
from nodeserver.wrapper.nodes.data.node_data_types import SuperSlotTypes
from nodeserver.wrapper.nodes.helpers.connection_manager import ConnectionManager
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import SlotData
from nodeserver.wrapper.nodes.helpers.node_manager import NodeMirrorManager
from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror, SlotMirror, SlotOutput

class NodeSlot[outputType: SlotOutput]:
    _output_class: Type[outputType]
    _version: int
    
    _output: outputType
    _mirror: SlotMirror

    def __init__(self, mirror: Optional[SlotMirror] = None, output_cls: Type[outputType] = SlotOutput) -> None:
        if mirror != None:
            self._mirror = mirror
        
        self._output_class = output_cls
        self._output = self._output_class()

# Gerado fora do node, no runtime (com base no output dos slots conectados, esse output é retirado do NodeOutput do node pai dos slots conectados)
class NodeInput(BaseModel): 
    # Slot Name: SlotInputType = SlotInputValue
    pass

# Gerado dentro do node no forward
class NodeOutput(BaseModel): 
    # Slot Name: SlotOutputType = SlotOutput
    pass

# TODO: Change node inputs to a NodeOutput class or NodeInputs class
class BaseNode[inputType: NodeInput, outputType: NodeOutput]:
    _version: int = 0
    _mirror: NodeMirror

    dirty: bool = True
    bypass_cache: bool = False
    class Slots:
        pass

    _slots: Slots
    slots: dict[str, NodeSlot]

    def __init__(self, mirror: NodeMirror | None = None):
        if mirror != None:
            self._mirror = mirror
            self._build_slots()

    def _build_slots(self):
        hints = get_type_hints(self.Slots, globalns=globals())
        self._slots = self.Slots()
        for attribute_name, hint in hints.items():
            slot_mirror = self._mirror.get_slot(attribute_name)
            if not slot_mirror:
                continue
            
            origin = get_origin(hint) or hint
            args = get_args(hint)

            actual_output_type = args[0] if args else SlotOutput
            slot_instance = origin(mirror=slot_mirror, output_cls=actual_output_type)
            
            setattr(self._slots, attribute_name, slot_instance)
    
    def pre_forward(self, input: dict[SlotMirror, dict[SlotMirror, SlotOutput]]):
        pass

    @abstractmethod
    def forwardV2(self, input: inputType) -> outputType:
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

    def self_validate(self, node_manager: NodeMirrorManager, conn_manager: ConnectionManager) -> bool:
        return True

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
