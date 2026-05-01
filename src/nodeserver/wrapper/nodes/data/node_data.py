from __future__ import annotations
from typing import Any

from nodeserver.wrapper.nodes.data.node_data_types import BaseDataType
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import NodeParameterData


class NodeParameter:
    _version: int
    type: BaseDataType
    _field_name: str
    
    _value: Any
    _data_model: NodeParameterData

    def __init__(self, field_data_model: NodeParameterData, field_name: str, value: Any):
        self._version = 0
        self._field_name = field_name
        self._data_model = field_data_model

        self._value = value
    
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value: Any):
        if self._value != new_value:
            self._value = new_value
            self._version += 1
    
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

    def get_parameter_value(self, param_name: str) -> Optional[Any]:
        parameter = self.parameters.get(param_name)
        if not parameter:
            return None
        
        return parameter.value

    def set_parameter_value(self, param_name: str, new_value: Any):
        parameter = self.parameters.get(param_name)
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
                data_model, key, raw_parameters.get(key, None)
            )

        return parsed_params