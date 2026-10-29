from enum import Enum


# TODO: pensar em uma forma melhor de definir os renderers.
# como é algo que depende da implementação do client, talvez isso nem deva estar
# no servidor. Mas ainda assim é relevante por enquanto, por isso vai ficar aqui
class DefaultRenderers(str, Enum):
    SCALAR = "scalar"
    ARRAY = "array"
    TEXT = "text"
    FILE = "file"
    NOT_IMPLEMENTED = "not_implemented"

# TODO: pensar em uma forma melhor de definir os DataTypes default
class DefaultDataTypes(str, Enum):
    FLOAT = "float"
    INT = "int"
    BOOLEAN = "boolean"
    TEXT = "text"
    UNKNOWN = "unknown"

    ARRAY = "array" # TODO: rename to ndarray
    FILE = "file"
    OPTIONS = "options" # FIXME: options não deveria ser um datatype e sim um tipo de parâmetro

    UINT = "uint" # deprecated
    CUSTOM = "custom"
