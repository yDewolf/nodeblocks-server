
from typing import Any, Generic, Optional, Type, TypeVar, get_args
from nodeserver.wrapper.nodes.data.node_data_types import DefaultDataTypes
from nodeserver.wrapper.nodes.node.base_nodes import SlotMirror
from nodeserver.api.node.abstract._slots import _SlotIO

class InputSlotIO[inputType: Any](_SlotIO[inputType, True]):
    _is_input = True

class OutputSlotIO[outputType: Any](_SlotIO[outputType, False]):
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
        
        args = get_args(self._output_class)
        self._io = self._output_class(raw_io_type=raw_io_type, is_input=args[1])

    def has_mirror(self) -> bool:
        return hasattr(self, "_mirror")

    def make_output_from_value(self, value: Any):
        self._io.value = value
        return self._io

class SlotConfig:
    def __init__(
        self, 
        slot_class: Optional[Type[NodeSlot]] = None,
        slot_io: Optional[Type[_SlotIO[Any, bool]]] = None,
        renderer_override: Optional[DefaultDataTypes] = None,
        is_input: bool = False, 
        max_inputs: int = 1, 
        **kwargs
    ):
        self.slot_class = slot_class
        self.slot_io = slot_io

        self.is_input = is_input
        self.extra_kwargs = kwargs

        self.renderer_override = renderer_override
        self.max_inputs = max_inputs if self.is_input else 0

def Input(max_inputs: int = 1, **kwargs):
    return SlotConfig(slot_class=NodeSlot, slot_io=_SlotIO, is_input=True, max_inputs=max_inputs, **kwargs)

def Output(renderer_override: Optional[DefaultDataTypes] = None, **kwargs):
    return SlotConfig(slot_class=NodeSlot, slot_io=_SlotIO, is_input=False, renderer_override=renderer_override, **kwargs)