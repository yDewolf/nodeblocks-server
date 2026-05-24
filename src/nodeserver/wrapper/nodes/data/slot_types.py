
from nodeserver.wrapper.nodes.data.node_data_types import BaseDataType, DataTypeUtils


class BaseSlotType:
    data_type: BaseDataType
    
    def __init__(self, data_type: BaseDataType) -> None:
        self.data_type = data_type


class SlotTypeUtils:
    @staticmethod
    def is_type_compatible_with(type_a: BaseSlotType, type_b: BaseSlotType):
        return DataTypeUtils.is_type_compatible_with(type_a.data_type, type_b.data_type)
