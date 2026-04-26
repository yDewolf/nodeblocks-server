from enum import Enum
from typing import Any, TypeVar, Literal

class DataTypes(str, Enum):
    FLOAT = "float"
    UINT = "uint"
    INT = "int"
    ARRAY = "array"
    FILE = "file"
    CUSTOM = "custom"
    UNKNOWN = "unknown"

class SuperSlotTypes(str, Enum):
    INPUT = "input_slot"
    OUTPUT = "output_slot"
    UNKNOWN = "unknown"

class DataGroup(Enum):
    NODE = DataTypes
    SLOT = SuperSlotTypes

class BaseDataType[group: DataGroup, superType: (DataTypes, SuperSlotTypes)]:
    type_name: str

    _data_group: TypeVar
    _super_type: superType
    _type_whitelist: list[superType] = []
    _name_whitelist: list[str] = []

    def __init__(self, type_name: str, super_type: superType, type_whitelist: list[superType], name_whitelist: list[str] = []):
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

    def __init__(self, type_name: str, data_type: BaseNodeType, super_type: SuperSlotTypes, type_whitelist: list[SuperSlotTypes], name_whitelist: list[str] = []):
        self.data_type = data_type
        super().__init__(type_name, super_type, type_whitelist, name_whitelist)



FLOAT_TYPE = BaseNodeType("float", DataTypes.FLOAT, [DataTypes.FLOAT])
INT_TYPE = BaseNodeType("int" , DataTypes.INT, [DataTypes.INT])
UINT_TYPE = BaseNodeType("uint" , DataTypes.UINT, [DataTypes.UINT])
ARRAY_TYPE = BaseNodeType("array" , DataTypes.ARRAY, [DataTypes.ARRAY])
FILE_TYPE = BaseNodeType("file" , DataTypes.FILE, [DataTypes.FILE])
UNKNOWN_TYPE = BaseNodeType("unknown" , DataTypes.UNKNOWN, [DataTypes.UNKNOWN])

INPUT_TYPE = BaseSlotType("input_slot", UNKNOWN_TYPE, SuperSlotTypes.INPUT, [SuperSlotTypes.OUTPUT])
OUTPUT_TYPE = BaseSlotType("output_slot", UNKNOWN_TYPE, SuperSlotTypes.OUTPUT, [SuperSlotTypes.INPUT])

class DataTypeUtils:
    @staticmethod
    def _match_super_type(type_str: str) -> DataTypes:
        match type_str.lower():
            case "float": return DataTypes.FLOAT
            case "int": return DataTypes.INT
            case "uint": return DataTypes.UINT
            case "array": return DataTypes.ARRAY
            case "file": return DataTypes.FILE
            case "custom": return DataTypes.CUSTOM
            case _:
                return DataTypes.UNKNOWN

    @staticmethod
    def _match_slot_super_type(type_str: str) -> SuperSlotTypes:
        match type_str.lower():
            case "input_slot": return SuperSlotTypes.INPUT
            case "output_slot": return SuperSlotTypes.OUTPUT
            case _:
                return SuperSlotTypes.UNKNOWN

    @staticmethod
    def _match_data_type_str(type_str: str) -> BaseNodeType:
        match type_str.lower():
            case "float": return FLOAT_TYPE
            case "int": return INT_TYPE
            case "uint": return UINT_TYPE
            case "array": return ARRAY_TYPE
            case _:
                return UNKNOWN_TYPE

    @staticmethod
    def _match_slot_type_str(type_str: str) -> BaseSlotType | None:
        match type_str.lower():
            case "input_slot": return INPUT_TYPE
            case "output_slot": return OUTPUT_TYPE
            case _:
                return None

    @staticmethod
    def is_type_compatible_with(type_a: BaseDataType[Any, Any], type_b: BaseDataType[Any, Any]) -> bool:
        # FIXME: Slot Compatibility might be broken
        if type_a._data_group != type_b._data_group:
            return False

        if type_a._type_whitelist.__contains__(type_b._super_type):
            return True

        if type_a._name_whitelist.__contains__(type_b.type_name):
            return True

        return False

    @staticmethod
    def _parse_type_whitelist(str_list: list[str], _type: type[DataTypes] | type[SuperSlotTypes]) -> tuple[list, list[str]]:
        type_whitelist: list = []
        name_whitelist: list[str] = []

        for element in str_list:
            if element == "":
                continue

            if element.startswith("#"):
                if _type is DataTypes:
                    type_whitelist.append(DataTypeUtils._match_super_type(element[1:]))
                    continue
                
                if _type is SuperSlotTypes:
                    type_whitelist.append(DataTypeUtils._match_slot_super_type(element[1:]))
                    continue

            name_whitelist.append(element)

        return type_whitelist, name_whitelist
    
