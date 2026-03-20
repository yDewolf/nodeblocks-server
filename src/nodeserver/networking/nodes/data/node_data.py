
from nodeserver.networking.nodes.data.node_data_types import BaseDataType
from nodeserver.networking.nodes.node_parser import NodeParameterData


class NodeParameter:
    type: BaseDataType
    _field_name: str
    
    _raw_field_data: NodeParameterData

    def __init__(self, field_data: NodeParameterData, field_name: str):
        self._field_name = field_name
        self._raw_field_data = field_data
        

class NodeData:
    parameters: dict[str, NodeParameter]

    def __init__(self, raw_parameters: dict[str, NodeParameterData]):
        self.parameters = NodeData.parse_parameters(raw_parameters)


    @staticmethod
    def parse_parameters(raw_parameters: dict[str, NodeParameterData]):
        pass