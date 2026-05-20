

from nodeserver.wrapper.nodes.data.node_data_types import BaseDataType, DataTypeUtils


class CustomDataType(BaseDataType):
    def __init__(self, type_name: str, super_type: str, _type_whitelist: list[str]):
        parsed_data_type = DataTypeUtils._match_data_type_str(super_type)
        type_whitelist, name_whitelist = DataTypeUtils._parse_type_whitelist(_type_whitelist)
        
        super().__init__(type_name, parsed_data_type._renderer, type_whitelist, name_whitelist)
