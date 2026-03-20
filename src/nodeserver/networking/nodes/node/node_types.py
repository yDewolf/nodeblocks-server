from enum import Enum
from nodeserver.networking.nodes.data.node_data_types import BaseDataType, SuperSlotTypes

class SlotType:
    type_name: str
    data_type: BaseDataType

    super_type: SuperSlotTypes

    type_whitelist: list[SuperSlotTypes]
    name_whitelist: list[str]

    def __init__(self, type: SuperSlotTypes, data_type: BaseDataType, slot_type_whitelisted: list[SuperSlotTypes], type_name: str = "default", name_whitelist: list[str] = []):
        self.super_type = type
        self.type_name = type_name
        
        self.data_type = data_type
        self.type_whitelist = slot_type_whitelisted
        self.name_whitelist = name_whitelist