
from typing import Any, Optional, Type, Union, get_args
from typing_extensions import get_origin

from nodeserver.wrapper.abstract.abstract_types import BaseValueWrapper
from nodeserver.wrapper.nodes.data.node_data_types import DataTypeUtils, DefaultDataTypes, DefaultRenderers, _match_renderer

class _SlotIO[valueType: Any, is_input: bool](BaseValueWrapper[valueType]) :
    _max_connections: int = 0
    _value_meta: Optional[dict[str, Any]] = None # TODO: this should be typesafe

    _is_input: bool = False
    
    _base_type: Optional[DefaultDataTypes] = None # Sets the respective generated DataType's Renderer
    _renderer: Optional[DefaultRenderers] = None

    def __init__(self, value: Optional[valueType] = None, max_connections: int = -1, raw_io_type: Type[Any] = Type, is_input: bool = False) -> None:
        self._max_connections = max_connections
        self._is_input = is_input
        super().__init__(value, raw_io_type)
        
    def _setup_type_variables(self):
        input_type = get_origin(self._raw_io_type)
        try:
            is_collection = issubclass(input_type, (list, tuple)) # type: ignore
            if self._max_connections == -1:
                if is_collection or not self._is_input:
                    self._max_connections = 0 # TODO: Can receive any amount of inputs

                if not is_collection and self._is_input:
                    self._max_connections = 1
            self._is_collection = is_collection

        except TypeError: 
            pass
        
        self._type_args = get_args(self._raw_io_type) if not self._type_args else self._type_args


    @property
    def value_meta(self):
        return self._value_meta

    @value_meta.setter
    def value_meta(self, new_value: dict):
        if self._value_meta != new_value:
            self._value_meta = new_value
            self._version += 1

    # This method should be overriden by other SlotIO classes 
    # to automatically generate meta from new values
    @classmethod
    def update_value_meta(cls, new_value: valueType) -> Optional[dict[str, Any]]:
        return None

    def get_base_type(self) -> DefaultDataTypes:
        if self._base_type:
            return self._base_type

        return DataTypeUtils._match_super_type(
            self.get_type().__name__
        )

    def get_renderer(self) -> DefaultRenderers:
        if self._renderer:
            return self._renderer
        
        return _match_renderer(self.get_base_type())

    def make_datatype_id(self) -> str:
        return f"{self.__class__.__name__}:{self.get_type().__name__}" + (f"_{self.get_base_type().value}" if self._base_type else "")

    def is_collection(self) -> bool:
        return self._max_connections == 0 or self._max_connections > 1