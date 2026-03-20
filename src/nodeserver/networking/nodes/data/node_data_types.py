from enum import Enum
from typing import Any, TypeVar, Literal

class DataTypes(Enum):
    FLOAT = 0
    UINT = 1
    INT = 2
    ARRAY = 3
    CUSTOM = 4
    UNKNOWN = 5

class SuperSlotTypes(Enum):
    INPUT = 0
    OUTPUT = 1
    UNKNOWN = 2

class DataGroup(Enum):
    NODE = DataTypes
    SLOT = SuperSlotTypes

class BaseDataType[group: DataGroup, superType: (DataTypes, SuperSlotTypes)]:
    type_name: str

    _data_group: TypeVar
    _super_type: superType
    _type_whitelist: list[DataTypes] = []
    _name_whitelist: list[str] = []

    def __init__(self, type_name: str, super_type: superType, type_whitelist: list[DataTypes], name_whitelist: list[str] = []):
        self.type_name = type_name

        self._data_group = group
        self._super_type = super_type
        self._type_whitelist = type_whitelist
        self._name_whitelist = name_whitelist

class BaseNodeType(BaseDataType[DataGroup.SLOT, DataTypes]):
    def __init__(self, type_name: str, super_type: DataTypes, type_whitelist: list[DataTypes], name_whitelist: list[str] = []):
        super().__init__(type_name, super_type, type_whitelist, name_whitelist)
    

class BaseSlotType(BaseDataType[DataGroup.SLOT, SuperSlotTypes]):
    data_type: BaseNodeType

    def __init__(self, type_name: str, data_type: BaseNodeType, super_type: SuperSlotTypes, type_whitelist: list[DataTypes], name_whitelist: list[str] = []):
        self.data_type = data_type
        super().__init__(type_name, super_type, type_whitelist, name_whitelist)



FLOAT_TYPE = BaseNodeType("float", DataTypes.FLOAT, [DataTypes.FLOAT])
INT_TYPE = BaseNodeType("int" , DataTypes.INT, [DataTypes.INT])
UINT_TYPE = BaseNodeType("uint" , DataTypes.UINT, [DataTypes.UINT])
ARRAY_TYPE = BaseNodeType("array" , DataTypes.ARRAY, [DataTypes.ARRAY])
UNKNOWN_TYPE = BaseNodeType("unknown" , DataTypes.UNKNOWN, [DataTypes.UNKNOWN])


class DataTypeUtils:
    @staticmethod
    def _parse_super_type(type_str: str) -> DataTypes:
        match type_str.lower():
            case "float": return DataTypes.FLOAT
            case "int": return DataTypes.INT
            case "uint": return DataTypes.UINT
            case "array": return DataTypes.ARRAY
            case "custom": return DataTypes.CUSTOM
            case _:
                return DataTypes.UNKNOWN

    @staticmethod
    def _match_data_type_str(type_str: str):
        match type_str.lower():
            case "float": return FLOAT_TYPE
            case "int": return INT_TYPE
            case "uint": return UINT_TYPE
            case "array": return ARRAY_TYPE
            case _:
                return UNKNOWN_TYPE

    @staticmethod
    def is_type_compatible_with(type_a: BaseDataType[Any, Any], type_b: BaseDataType[Any, Any]) -> bool:
        if type_a._data_group != type_b._data_group:
            return False

        if type_a._type_whitelist.__contains__(type_b._super_type):
            return True

        if type_a._name_whitelist.__contains__(type_b.type_name):
            return True

        return False

# class CustomNodeDataType(BaseDataType[DataGroup.NODE]):
#     def __init__(self, type_name: str, super_type: DataTypes, type_whitelist: list[str]) -> None:
#         parsed_type_whitelist, name_whitelist = CustomNodeDataType._parse_type_whitelist(type_whitelist)

#         super().__init__(type_name, super_type, parsed_type_whitelist, name_whitelist)

#     @staticmethod
#     def _parse_type_whitelist(str_list: list[str]) -> tuple[list[DataTypes], list[str]]:
#         type_whitelist: list[DataTypes] = []
#         name_whitelist: list[str] = []

#         for element in str_list:
#             if element == "":
#                 continue

#             if element.startswith("#"):
#                 type_whitelist.append(DataTypeUtils._parse_super_type(element[:1]))
#                 continue

#             name_whitelist.append(element)

#         return type_whitelist, name_whitelist
    
