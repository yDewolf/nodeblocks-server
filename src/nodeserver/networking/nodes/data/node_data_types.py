from enum import Enum

class DataTypes(Enum):
    FLOAT = 0
    UINT = 1
    INT = 2
    ARRAY = 3
    CUSTOM = 4
    UNKNOWN = 5


class NodeDataType:
    type_name: str

    _super_type: DataTypes = DataTypes.UNKNOWN
    _type_whitelist: list[DataTypes] = []
    _name_whitelist: list[str] = []

    def __init__(self, type_name: str, super_type: DataTypes, type_whitelist: list[DataTypes], name_whitelist: list[str] = []):
        self.type_name = type_name

        self._super_type = super_type
        self._type_whitelist = type_whitelist
        self._name_whitelist = name_whitelist
    
    # TODO
    # def is_compatbile_with(type: NodeDataType):
    #     pass

