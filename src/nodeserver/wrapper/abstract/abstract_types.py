
from typing import Any, Optional, Type, Union, get_args, get_origin


class BaseValueWrapper[valueType: Any]:
    _version: int
    _value: Optional[valueType] = None

    _raw_io_type: Type[Any] = Type
    _is_optional: Optional[bool] = None
    _is_collection: Optional[bool] = None

    _type_args: Optional[tuple[Any, ...]] = None

    def __init__(self, value: Optional[valueType] = None, raw_io_type: Type[Any] = Type) -> None:
        self._value = value
        self._version = 0

        self._raw_io_type = raw_io_type
        self._setup_type_variables()
        
    def _setup_type_variables(self):
        self._type_args = get_args(self._raw_io_type) if not self._type_args else self._type_args
        self._update_is_optional()

    def is_collection(self) -> bool:
        if self._is_collection:
            return self._is_collection

        try:
            is_collection = issubclass(input_type, (list, tuple)) # type: ignore
            self._is_collection = is_collection

        except TypeError: 
            pass

        return is_collection

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

    def is_optional(self) -> bool:
        if self._is_optional != None:
            return self._is_optional

        self._is_optional = self._update_is_optional()                
        return self._is_optional

    def _update_is_optional(self) -> bool:
        if get_origin(self._raw_io_type) is Union:
            # Check if None (type(None)) is one of the arguments in the Union
            self._is_optional = type(None) in get_args(self._raw_io_type)
            return self._is_optional

        return False
