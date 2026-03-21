
from nodeserver.networking.nodes.data.node_data_types import BaseNodeType, BaseSlotType, DataTypeUtils, SuperSlotTypes


class CustomSlotType(BaseSlotType):
    def __init__(self, type_name: str, data_type: str, super_type: str, _type_whitelist: list[str]):
        parsed_data_type = DataTypeUtils._match_data_type_str(data_type)
        parsed_super_type = DataTypeUtils._match_slot_super_type(super_type)
        type_whitelist, name_whitelist = DataTypeUtils._parse_type_whitelist(_type_whitelist, SuperSlotTypes)
        
        super().__init__(type_name, parsed_data_type, parsed_super_type, type_whitelist, name_whitelist)