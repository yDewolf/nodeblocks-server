from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers
from nodeserver.protocols.helpers.datatype_helper import DatatypeHelper
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec
from nodeserver.protocols.manifest.node.node_manifest import NodeTypeSpec

class TypeRegistry:
    # type_id -> spec
    data_types: dict[str, DataTypeSpec]
    node_types: dict[str, NodeTypeSpec]

    def __init__(self):
        self.data_types = {}
        self.node_types = {}
        
        self._register_core_types()

    def _register_core_types(self):
        self.register_data_type("core.int", DatatypeHelper.create_spec(DefaultDataTypes.INT, DefaultRenderers.SCALAR, ["core.float", "core.int"]))
        self.register_data_type("core.float", DatatypeHelper.create_spec(DefaultDataTypes.FLOAT, DefaultRenderers.SCALAR))
        self.register_data_type("core.bool", DatatypeHelper.create_spec(DefaultDataTypes.BOOLEAN, DefaultRenderers.TEXT))
        self.register_data_type("core.array", DatatypeHelper.create_spec(DefaultDataTypes.ARRAY, DefaultRenderers.ARRAY))
        self.register_data_type("core.file", DatatypeHelper.create_spec(DefaultDataTypes.FILE, DefaultRenderers.NOT_IMPLEMENTED))
        self.register_data_type("core.unknown", DatatypeHelper.create_spec(DefaultDataTypes.UNKNOWN, DefaultRenderers.NOT_IMPLEMENTED))


    # TODO: implementar os plugins para registrar automaticamente os specs aqui
    def register_data_type(self, type_id: str, spec: DataTypeSpec):
        if type_id in self.data_types:
            raise ValueError(f"DataType '{type_id}' is already registered")

        self.data_types[type_id] = spec


    def are_types_compatible(self, source_type: str, target_type: str) -> bool:
        source_spec = self.data_types.get(source_type)
        target_spec = self.data_types.get(target_type)
        if not source_spec or not target_spec:
            return False

        return DatatypeHelper.are_types_compatible(source_spec, target_spec)
