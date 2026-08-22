from __future__ import annotations
from typing import Any, Optional, Type

from nodeserver.api.node.node_exceptions import MissingParameter, ParameterException
from nodeserver.wrapper.abstract.abstract_types import BaseValueWrapper
from nodeserver.wrapper.nodes.data.node_data_types import BaseDataType
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import NodeParameterData


class NodeParameter[valueType: Any](BaseValueWrapper[valueType]):
    type: BaseDataType
    _field_id: str

    _data_model: NodeParameterData

    def __init__(self, field_data_model: NodeParameterData, field_id: str, value: Optional[valueType], raw_io_type: Type[Any] = Type):
        super().__init__(value, raw_io_type)
        self._field_id = field_id
        self._data_model = field_data_model

    def self_validate(self) -> Optional[ParameterException]:
        if not self.is_optional() and self._value == None:
            return MissingParameter(self)

        return None

    
class NodeData:
    _version: int = 0
    param_model: dict[str, NodeParameterData]
    parameters: dict[str, NodeParameter]

    def __init__(self, raw_parameters: dict[str, NodeParameterData]):
        self.param_model = raw_parameters

    @staticmethod
    def from_model(model: NodeData) -> NodeData:
        data = NodeData(model.param_model)
        return data

    def map_parameters(self) -> dict[str, Any]:
        return {key: parameter.value for key, parameter in self.parameters.items()}

    def get_parameter_value(self, param_id: str, default: Any = None) -> Any:
        parameter = self.parameters.get(param_id)
        if not parameter:
            return default
        
        return parameter.value

    def set_parameter_value(self, param_id: str, new_value: Any):
        parameter = self.parameters.get(param_id)
        if not parameter:
            return
        
        if parameter.value != new_value:
            parameter.value = new_value
            self._version += 1

    def parse_parameters(self, raw_parameters: dict[str, Any]):
        self.parameters = NodeData._parse_parameters(self.param_model, raw_parameters)

    @staticmethod
    def _parse_parameters(param_model: dict[str, NodeParameterData], raw_parameters: dict[str, Any]) -> dict[str, NodeParameter]:
        parsed_params: dict[str, NodeParameter] = {}
        for key in param_model:
            data_model = param_model.get(key)
            if not data_model:
                continue

            parsed_params[key] = NodeParameter(
                data_model, key, raw_parameters.get(key, None), data_model.raw_io_type or Type
            )

        return parsed_params