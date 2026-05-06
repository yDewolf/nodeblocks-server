
from typing import Any, Optional, Type

from nodeserver.wrapper.nodes.node.base_nodes import SlotMirror

class SlotIO[inputType: Any, valueType: Any]:
    _version: int
    _value: Optional[valueType] = None

    def __init__(self) -> None:
        self._version = 0

    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, new_value: valueType):
        if self._value != new_value:
            self._value = new_value
            self._version += 1

class NodeSlot[outputType: SlotIO]:
    _output_class: Type[outputType]
    _version: int
    
    _output: outputType
    _mirror: SlotMirror

    def __init__(self, mirror: Optional[SlotMirror] = None, output_cls: Type[outputType] = SlotIO) -> None:
        if mirror != None:
            self._mirror = mirror
        
        self._output_class = output_cls
        self._output = self._output_class()


class SlotConfig:
    def __init__(self, slot_class: Optional[Type[NodeSlot]] = None, is_input: bool = True, **kwargs):
        self.slot_class = slot_class # Se None, o gerador usa o padrão NodeSlot
        self.is_input = is_input
        self.extra_kwargs = kwargs

def Input(slot_cls: Optional[Type[NodeSlot]] = None, **kwargs):
    return SlotConfig(slot_class=slot_cls, is_input=True, **kwargs)

def Output(slot_cls: Optional[Type[NodeSlot]] = None, **kwargs):
    return SlotConfig(slot_class=slot_cls, is_input=False, **kwargs)