
from typing import Any, Optional, Type, TypeVar, get_args, get_origin

from nodeserver.wrapper.nodes.node.base_nodes import SlotMirror

class SlotIO[inputType: Any, valueType: Any]:
    _max_inputs: int = 1
    _version: int
    _value: Optional[valueType] = None

    _raw_io_type: Type[Any]

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

class NodeSlot[outputType: SlotIO]:
    _output_class: Type[outputType]
    _version: int
    
    _output: outputType
    _mirror: SlotMirror

    def __init__(self, mirror: Optional[SlotMirror] = None, output_cls: Type[outputType] = SlotIO, raw_io_type: Type[Any] = Type) -> None:
        if mirror != None:
            self._mirror = mirror
        
        self._output_class = output_cls
        self._output = self._output_class(raw_io_type=raw_io_type)


    def make_output_from_value(self, value: Any):
        self._output.value = value
        return self._output

class SlotConfig:
    def __init__(self, slot_class: Optional[Type[NodeSlot]] = None, is_input: bool = True, **kwargs):
        self.slot_class = slot_class
        self.is_input = is_input
        self.extra_kwargs = kwargs

def Input(slot_cls: Optional[Type[NodeSlot]] = None, max_inputs: int = 1, **kwargs):
    return SlotConfig(slot_class=slot_cls, is_input=True, max_inputs=max_inputs, **kwargs)

def Output(slot_cls: Optional[Type[NodeSlot]] = None, **kwargs):
    return SlotConfig(slot_class=slot_cls, is_input=False, **kwargs)