from enum import Enum

class DefaultDataTypes(str, Enum):
    FLOAT = "float"
    UINT = "uint"
    INT = "int"
    ARRAY = "array"
    FILE = "file"
    CUSTOM = "custom"
    TEXT = "text"
    OPTIONS = "options"
    UNKNOWN = "unknown"

class DefaultRenderers(str, Enum):
    SCALAR = "scalar"
    ARRAY = "array"
    TEXT = "text"
    NOT_IMPLEMENTED = "not_implemented"

def _match_renderer(base_type: DefaultDataTypes) -> DefaultRenderers:
    match base_type:
        case DefaultDataTypes.FLOAT: return DefaultRenderers.SCALAR
        case DefaultDataTypes.INT: return DefaultRenderers.SCALAR
        case DefaultDataTypes.UINT: return DefaultRenderers.SCALAR
        case DefaultDataTypes.ARRAY: return DefaultRenderers.ARRAY
        case _:
            return DefaultRenderers.NOT_IMPLEMENTED

class BaseDataType:
    type_id: str

    base: DefaultDataTypes # Used to set the DataTypeData renderer
    renderer: DefaultRenderers
    _type_whitelist: list[DefaultDataTypes] = []
    _name_whitelist: list[str] = []

    def __init__(self, type_name: str, base_type: DefaultDataTypes, type_whitelist: list[DefaultDataTypes], name_whitelist: list[str] = [], renderer: DefaultRenderers = DefaultRenderers.NOT_IMPLEMENTED):
        self.type_id = type_name
        
        if renderer == DefaultRenderers.NOT_IMPLEMENTED:
            renderer = _match_renderer(base_type)
        
        self.renderer = renderer
        
        self.base = base_type
        self._type_whitelist = type_whitelist
        self._name_whitelist = name_whitelist

# FIXME: Refatorar esse BaseNodeType para virar algo como um ParameterType ou algo do tipo
FLOAT_TYPE = BaseDataType("float", DefaultDataTypes.FLOAT, [DefaultDataTypes.FLOAT])
INT_TYPE = BaseDataType("int" , DefaultDataTypes.INT, [DefaultDataTypes.INT])
UINT_TYPE = BaseDataType("uint" , DefaultDataTypes.UINT, [DefaultDataTypes.UINT])
ARRAY_TYPE = BaseDataType("array" , DefaultDataTypes.ARRAY, [DefaultDataTypes.ARRAY])
FILE_TYPE = BaseDataType("file" , DefaultDataTypes.FILE, [DefaultDataTypes.FILE])
TEXT_TYPE = BaseDataType("text" , DefaultDataTypes.TEXT, [DefaultDataTypes.TEXT])
UNKNOWN_TYPE = BaseDataType("unknown" , DefaultDataTypes.UNKNOWN, [DefaultDataTypes.UNKNOWN])

class DataTypeUtils:
    @staticmethod
    def _match_super_type(type_str: str) -> DefaultDataTypes:
        match type_str.lower():
            case "float": return DefaultDataTypes.FLOAT
            case "int": return DefaultDataTypes.INT
            case "uint": return DefaultDataTypes.UINT
            case "array": return DefaultDataTypes.ARRAY
            case "file": return DefaultDataTypes.FILE
            case "text": return DefaultDataTypes.TEXT
            case "custom": return DefaultDataTypes.CUSTOM
            case _:
                return DefaultDataTypes.UNKNOWN

    @staticmethod
    def _match_data_type_str(type_str: str) -> BaseDataType:
        match type_str.lower():
            case "float": return FLOAT_TYPE
            case "int": return INT_TYPE
            case "uint": return UINT_TYPE
            case "array": return ARRAY_TYPE
            case "text": return TEXT_TYPE
            case "file": return FILE_TYPE
            case _:
                return UNKNOWN_TYPE

    @staticmethod
    def is_type_compatible_with(type_a: BaseDataType, type_b: BaseDataType) -> bool:
        if type_a._type_whitelist.__contains__(type_b.base):
            return True

        if type_a._name_whitelist.__contains__(type_b.type_id):
            return True

        return False

    @staticmethod
    def _parse_type_whitelist(str_list: list[str]) -> tuple[list, list[str]]:
        type_whitelist: list = []
        name_whitelist: list[str] = []

        for element in str_list:
            if element == "":
                continue

            if element.startswith("#"):
                type_whitelist.append(DataTypeUtils._match_super_type(element[1:]))

            name_whitelist.append(element)

        return type_whitelist, name_whitelist
    
