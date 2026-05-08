
from typing import Any, Generic, Optional, Type, TypeVar
from nodeserver.wrapper.nodes.data.node_data_types import BaseNodeType
from nodeserver.wrapper.nodes.node.base_nodes import SlotMirror
from nodeserver.api.node.abstract._slots import _SlotIO

class InputSlotIO[inputType: Any](_SlotIO[inputType, None]):
    _is_input = True

class OutputSlotIO[outputType: Any](_SlotIO[None, outputType]):
    _is_input = False

T_SlotIO = TypeVar("T_SlotIO", bound=_SlotIO, default=_SlotIO)
class NodeSlot(Generic[T_SlotIO]):
    _output_class: Type[T_SlotIO]
    _version: int
    
    _io: T_SlotIO
    _mirror: SlotMirror

    def __init__(self, mirror: Optional[SlotMirror] = None, output_cls: Type[T_SlotIO] = _SlotIO, raw_io_type: Type[Any] = Type) -> None:
        if mirror != None:
            self._mirror = mirror
        
        self._output_class = output_cls
        self._io = self._output_class(raw_io_type=raw_io_type)

    def has_mirror(self) -> bool:
        return hasattr(self, "_mirror")

    def make_output_from_value(self, value: Any):
        self._io.value = value
        return self._io

class SlotConfig:
    def __init__(self, slot_class: Optional[Type[NodeSlot]] = None, is_input: bool = False, max_inputs: int = 1, datatype_override: Optional[BaseNodeType] = None, **kwargs):
        self.slot_class = slot_class
        self.is_input = is_input
        self.extra_kwargs = kwargs
        self.datatype_override = datatype_override

        self.max_inputs = max_inputs if self.is_input else 0

def Input(slot_cls: Optional[Type[NodeSlot]] = None, max_inputs: int = 1, datatype_override: Optional[BaseNodeType] = None, **kwargs):
    return SlotConfig(slot_class=slot_cls, is_input=True, datatype_override=datatype_override, max_inputs=max_inputs, **kwargs)

def Output(slot_cls: Optional[Type[NodeSlot]] = None, datatype_override: Optional[BaseNodeType] = None, **kwargs):
    return SlotConfig(slot_class=slot_cls, is_input=False, datatype_override=datatype_override, **kwargs)