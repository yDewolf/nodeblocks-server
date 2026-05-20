
from nodeserver.wrapper.nodes.data.node_data_types import BaseDataType


class BaseSlotType:
    data_type: BaseDataType
    
    def __init__(self, data_type: BaseDataType) -> None:
        self.data_type = data_type