from abc import abstractmethod
import json
import os
import pathlib
from typing import Annotated, Any, Optional, Type, get_args, get_origin, get_type_hints

from pydantic import BaseModel

from nodeserver.api.internal.instance_state import InternalNodeState
from nodeserver.api.node.node_utils import NodeUtils
from nodeserver.api.node.slots import NodeSlot, SlotConfig, SlotIO
from nodeserver.wrapper.nodes.data.node_data_types import SuperSlotTypes
from nodeserver.wrapper.nodes.helpers.connection_manager import ConnectionManager
from nodeserver.wrapper.nodes.helpers.node_manager import NodeMirrorManager
from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror, SlotMirror

class _Node[inputType: BaseModel, outputType: BaseModel]:
    _version: int = 0
    _mirror: NodeMirror

    dirty: bool = True
    bypass_cache: bool = False
    
    class Slots:
        pass

    _slots: Slots

    def __init__(self, mirror: NodeMirror | None = None):
        self._slots = self.Slots()
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

            actual_output_type = args[0] if args else SlotIO
            slot_instance = origin(mirror=slot_mirror, output_cls=actual_output_type)
            
            setattr(self._slots, attribute_name, slot_instance)

    def slot(self, name: str) -> NodeSlot:
        slot = getattr(self._slots, name)
        if not isinstance(slot, NodeSlot):
            raise Exception(f"Tried to access an attribute ({name} in {self.__class__}) that is not a NodeSlot")
        
        if slot == None:
            raise Exception(f"Slot with name '{name}' doesn't exist for node ({self.__class__})")
        
        return slot


    @abstractmethod
    def pre_forward(self, input: inputType):
        pass

    @abstractmethod
    def forward(self, input: inputType) -> outputType:
        pass

    @abstractmethod
    def post_forward(self):
        pass


    @abstractmethod
    def self_validate(self, node_manager: NodeMirrorManager, conn_manager: ConnectionManager) -> bool:
        return True

    # Override these on your Node class:
    # Your load state logic
    @abstractmethod
    def load_state(self, root_state_path: str, state: InternalNodeState):
        if state.relative_state_path:
            my_state_file_path = os.path.join(root_state_path, state.relative_state_path)
            print(my_state_file_path)
            # Open file and load stuff


    # Should have save logic
    @abstractmethod
    def save_state(self, root_state_path: str) -> Optional[InternalNodeState]:
        state = self.get_state()
        if state:
            my_state_file_path, filename = NodeUtils.make_state_file_path(self._mirror, root_state_path, "json")
            state.relative_state_path = str(pathlib.Path(my_state_file_path).relative_to(root_state_path))
            
            with open(my_state_file_path, "w") as file:
                file.write(json.dumps({"some": "data"}))

        # Do some Save stuff if you need to
        return state

    # Shouldn't have save logic
    @abstractmethod
    def get_state(self) -> Optional[InternalNodeState]:
        return InternalNodeState(
            relative_state_path=None,
            state_data=None
        )

    def get_execution_hash(self, output_cache: dict[SlotMirror, SlotIO]) -> int:
        input_versions = 0
        slots_version = 0
        for slot in self._mirror.slots.get(SuperSlotTypes.INPUT, []):
            slots_version += slot._version
            for conn in slot.connections:
                cached = output_cache.get(conn)
                if cached: input_versions += cached._version
        
        return (self._version + self._mirror.data._version + input_versions + slots_version)

    def resolve_inputs(self, output_cache: dict) -> dict:
        raw_inputs = {}
        for slot in self._mirror.slots.get(SuperSlotTypes.INPUT, []):
            values = [output_cache[conn].value for conn in slot.connections if conn in output_cache]
            if not values: raw_inputs[slot.slot_name] = None

            real_slot = self.slot(slot.slot_name)
            # FIXME: help me
            input_type: Type[Any] = real_slot._output.get_type()
            origin = get_origin(input_type) or input_type
            try:
                is_collection = issubclass(origin, (list, tuple))
            except TypeError:
                print("oi")
                is_collection = False

            if is_collection:
                raw_inputs[slot.slot_name] = values[:real_slot._output._max_inputs]
                if len(values) > real_slot._output._max_inputs:
                    # FIXME: Trocar isso aqui por um logger
                    print(f"WARNING: Shrinking node inputs for slot {slot}")
                
                continue

            raw_inputs[slot.slot_name] = values[0]
        
        return raw_inputs


class NoInput(BaseModel):
    pass

class NoOutput(BaseModel):
    pass

class BaseNode[inputType: BaseModel, outputType: BaseModel](_Node[inputType, outputType]):
    InputModel: Type[BaseModel] = NoInput
    OutputModel: Type[BaseModel] = NoOutput
    _slot_definitions: dict[str, Any]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        class GeneratedSlots:
            pass
        
        cls._slot_definitions = {}
        NodeUtils.process_model(cls.InputModel, default_is_input=True, generatedSlots=GeneratedSlots, _slot_definitions=cls._slot_definitions)
        NodeUtils.process_model(cls.OutputModel, default_is_input=False, generatedSlots=GeneratedSlots, _slot_definitions=cls._slot_definitions)
        
        cls.Slots = GeneratedSlots # type: ignore
    
    def _build_slots(self):
        for name, spec in self._slot_definitions.items():
            slot_mirror = self._mirror.get_slot(name)
            if not slot_mirror: continue

            instance = spec["class"](
                mirror=slot_mirror, 
                output_cls=spec["io"],
                raw_io_type=spec["raw_io_type"],
                **spec["args"]
            )

            setattr(self._slots, name, instance)
    
    def _parse_inputs(self, raw_input_data: dict) -> BaseModel:
        return self.InputModel(**raw_input_data)

    @abstractmethod
    def forward(self, input_data: inputType) -> outputType:
        pass
