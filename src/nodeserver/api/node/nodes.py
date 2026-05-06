from abc import abstractmethod
import json
import os
import pathlib
from typing import Annotated, Any, Optional, Type, get_args, get_origin, get_type_hints

from pydantic import BaseModel

from nodeserver.api.internal.instance_state import InternalNodeState
from nodeserver.api.node.node_utils import NodeUtils
from nodeserver.api.node.slots import NodeSlot, SlotConfig, SlotIO
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
    slots: dict[str, NodeSlot]

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
        slot = self.slots.get(name)
        if slot == None:
            raise Exception(f"Slot with name '{name}' doesn't exist for node ({self.__class__})")
        
        return slot


    @abstractmethod
    def pre_forward(self, input: dict[SlotMirror, dict[SlotMirror, SlotIO]]):
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


class BaseNode[inputType: BaseModel, outputType: BaseModel](_Node[inputType, outputType]):
    InputModel: Type[BaseModel] = BaseModel
    OutputModel: Type[BaseModel] = BaseModel
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
                **spec["args"]
            )
            setattr(self._slots, name, instance)
    
    def _parse_inputs(self, raw_input_data: dict) -> BaseModel:
        return self.InputModel(**raw_input_data)

    @abstractmethod
    def forward(self, input_data: inputType) -> outputType:
        pass
