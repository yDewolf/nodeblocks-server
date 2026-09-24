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
        # TODO: remover isso daqui e criar um plugin core
        self.register_data_type(DatatypeHelper.create_spec("core", "int", DefaultDataTypes.INT, DefaultRenderers.SCALAR, ["core.float", "core.int"]))
        self.register_data_type(DatatypeHelper.create_spec("core", "float", DefaultDataTypes.FLOAT, DefaultRenderers.SCALAR))
        self.register_data_type(DatatypeHelper.create_spec("core", "bool", DefaultDataTypes.BOOLEAN, DefaultRenderers.TEXT))
        self.register_data_type(DatatypeHelper.create_spec("core", "array", DefaultDataTypes.ARRAY, DefaultRenderers.ARRAY))
        self.register_data_type(DatatypeHelper.create_spec("core", "file", DefaultDataTypes.FILE, DefaultRenderers.NOT_IMPLEMENTED))
        self.register_data_type(DatatypeHelper.create_spec("core", "unknown", DefaultDataTypes.UNKNOWN, DefaultRenderers.NOT_IMPLEMENTED))


    # TODO: implementar os plugins para registrar automaticamente os specs aqui
    def register_data_type(self, spec: DataTypeSpec):
        if spec.id in self.data_types:
            raise ValueError(f"DataType '{spec.id}' is already registered")

        self.data_types[spec.id] = spec


    def are_types_compatible(self, source_type: str, target_type: str) -> bool:
        source_spec = self.data_types.get(source_type)
        target_spec = self.data_types.get(target_type)
        if not source_spec or not target_spec:
            return False

        return DatatypeHelper.are_types_compatible(source_spec, target_spec)
