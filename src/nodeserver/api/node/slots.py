
from typing import Any, Generic, Optional, Type, TypeVar
from nodeserver.wrapper.nodes.data.node_data_types import BaseNodeType
from nodeserver.wrapper.nodes.node.base_nodes import SlotMirror

class _SlotIO[inputType: Any, valueType: Any]:
    _max_inputs: int = 1
    _version: int
    _value: Optional[valueType] = None

    _datatype_override: Optional[BaseNodeType] = None
    _raw_io_type: Type[Any] = Type
    _is_input: bool = False

    def __init__(self, value: Optional[valueType] = None, max_inputs: int = 1, raw_io_type: Type[Any] = Type) -> None:
        self._max_inputs = max_inputs
        self._value = value
        self._version = 0

        self._raw_io_type = raw_io_type

    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, new_value: valueType):
        if self._value != new_value:
            self._value = new_value
            self._version += 1

    # FIXME:
    def get_type(self) -> type[Any]:
        return self._raw_io_type

class InputSlotIO[inputType: Any](_SlotIO[inputType, None]):
    _is_input = True

class OutputSlotIO[outputType: Any](_SlotIO[None, outputType]):
    _is_input = False

T_SlotIO = TypeVar("T_SlotIO", bound=_SlotIO, default=_SlotIO)
class NodeSlot(Generic[T_SlotIO]):
    _output_class: Type[T_SlotIO]
    _version: int
    
    _output: T_SlotIO
    _mirror: SlotMirror

    def __init__(self, mirror: Optional[SlotMirror] = None, output_cls: Type[T_SlotIO] = _SlotIO, raw_io_type: Type[Any] = Type) -> None:
        if mirror != None:
            self._mirror = mirror
        
        self._output_class = output_cls
        self._output = self._output_class(raw_io_type=raw_io_type)

    def has_mirror(self) -> bool:
        return hasattr(self, "_mirror")

    def make_output_from_value(self, value: Any):
        self._output.value = value
        return self._output

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