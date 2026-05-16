from abc import abstractmethod
import logging
from typing import Any, Optional, Type

from pydantic import BaseModel

from nodeserver.api.instance.instance_runtime import _ReadonlyContext, RuntimeContext
from nodeserver.api.node.node_utils import NodeUtils
from nodeserver.wrapper.nodes.data.node_data_types import UNKNOWN_TYPE, BaseSlotType, DataTypeUtils, SuperSlotTypes
from nodeserver.api.node.abstract._nodes import _Node
from nodeserver.api.node.slots import NodeSlot
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import SlotData
from nodeserver.wrapper.nodes.node.base_nodes import SlotMirror

logger = logging.getLogger("nds.nodes")


class NoInput(BaseModel):
    pass

class NoOutput(BaseModel):
    pass

class NoParameters(BaseModel):
    pass
# TODO:

class BaseNode[inputType: BaseModel, outputType: BaseModel](_Node[inputType, outputType]):
    InputModel: Type[BaseModel] = NoInput
    OutputModel: Type[BaseModel] = NoOutput
    _parameters: NoParameters
    _slot_definitions: dict[str, Any]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        class GeneratedSlots:
            pass
        
        cls._slot_definitions = {}
        NodeUtils.process_model(cls.InputModel, default_is_input=True, slots_class=GeneratedSlots, _slot_definitions=cls._slot_definitions)
        NodeUtils.process_model(cls.OutputModel, default_is_input=False, slots_class=GeneratedSlots, _slot_definitions=cls._slot_definitions)
        
        cls._Slots = cls.Slots
        cls.Slots = GeneratedSlots # type: ignore
    
    def _build_slots(self):
        super()._build_slots()
        for name, spec in self._slot_definitions.items():
            slot_mirror: Optional[SlotMirror] = None
            if self.has_mirror():
                slot_mirror = self._mirror.get_slot(name)
                if not slot_mirror: continue

            instance: NodeSlot = self._build_slot_instance_from_spec(spec, slot_mirror)

            setattr(self._slots, name, instance)
    
    @classmethod
    def _build_slot_instance_from_spec(cls, spec: dict, slot_mirror: Optional[SlotMirror]):
        instance: NodeSlot = spec["class"](
            mirror=slot_mirror, 
            output_cls=spec["io"],
            **spec["args"]
        )

        instance._io._max_connections = spec["max_inputs"]
        instance._io._raw_io_type = spec["raw_type"]
        datatype_override = spec.get("datatype_override")
        instance._io._datatype_override = datatype_override
        if datatype_override and instance.has_mirror():
            instance._mirror.data_type = datatype_override

        return instance

    @classmethod
    def _add_cls_slot_types(cls, super_types: dict[str, BaseSlotType], slot_types: dict[str, SlotData]):
        for name, spec in cls._slot_definitions.items():
            slot_instance = cls._build_slot_instance_from_spec(spec, None)
            cls._add_slot_types(name, slot_instance, super_types, slot_types)

    def _parse_inputs(self, raw_input_data: dict) -> BaseModel:
        return self.InputModel(**raw_input_data)

    @abstractmethod
    def forward(self, input: inputType) -> outputType:
        pass
