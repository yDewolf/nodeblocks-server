
from typing import Any, Optional, Type, get_args
from typing_extensions import get_origin

from nodeserver.wrapper.nodes.data.node_data_types import BaseNodeType


class _SlotIO[inputType: Any, valueType: Any]:
    _max_connections: int = 0
    _version: int
    _value: Optional[valueType] = None

    _datatype_override: Optional[BaseNodeType] = None
    _raw_io_type: Type[Any] = Type
    _is_input: bool = False
    
    _type_args: Optional[tuple[Any, ...]] = None

    def __init__(self, value: Optional[valueType] = None, max_connections: int = -1, raw_io_type: Type[Any] = Type) -> None:
        self._max_connections = max_connections
        self._value = value
        self._version = 0

        self._raw_io_type = raw_io_type
        self._setup_type_variables()
        
    def _setup_type_variables(self):
        input_type = get_origin(self._raw_io_type)
        try:
            is_collection = issubclass(input_type, (list, tuple))
            if self._max_connections == -1:
                if is_collection or not self._is_input:
                    self._max_connections = 0 # TODO: Can receive any amount of inputs

                if not is_collection and self._is_input:
                    self._max_connections = 1

        except TypeError: 
            pass
        
        self._type_args = get_args(self._raw_io_type) if not self._type_args else self._type_args

    
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
        self._type_args = get_args(self._raw_io_type) if not self._type_args else self._type_args
        if self._type_args:
            return self._type_args[0]
        
        return self._raw_io_type

    def is_collection(self) -> bool:
        return self._max_connections == 0 or self._max_connections > 1
