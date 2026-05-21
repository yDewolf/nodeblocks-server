

from typing import Optional

from nodeserver.wrapper.nodes.data.node_data_types import UNKNOWN_TYPE, BaseDataType, DataTypeUtils


class CustomDataType(BaseDataType):
    def __init__(self, type_id: str, super_type: Optional[str], _type_whitelist: list[str]):
        parsed_data_type = UNKNOWN_TYPE
        if super_type:
            parsed_data_type = DataTypeUtils._match_data_type_str(super_type)
        
        type_whitelist, name_whitelist = DataTypeUtils._parse_type_whitelist(_type_whitelist)
        
        super().__init__(type_id, parsed_data_type.base, type_whitelist, name_whitelist)
