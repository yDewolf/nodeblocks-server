from typing import Optional, Type

from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers
from nodeserver.protocols.helpers.datatype_helper import DatatypeHelper
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec
from nodeserver.protocols.manifest.node.node_manifest import NodeTypeSpec

class TypeRegistry:
    # type_id -> spec
    data_types: dict[str, DataTypeSpec]
    node_types: dict[str, NodeTypeSpec]

    node_logic_classes: dict[str, Type[BaseNode]]
    python_type_map: dict[type, DataTypeSpec]

    def __init__(self):
        self.data_types = {}
        self.node_types = {}

        self.node_logic_classes = {}
        self.python_type_map = {}
        
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
    def register_data_type(self, spec: DataTypeSpec, python_type: Optional[type] = None):
        if spec.fqn in self.data_types:
            raise ValueError(f"DataType '{spec.fqn}' is already registered")

        self.data_types[spec.fqn] = spec
        if python_type is not None:
            self.python_type_map[python_type] = spec
    

    def register_node_type(self, spec: NodeTypeSpec, logic_class: Type[BaseNode]):
        if spec.fqn in self.data_types:
            raise ValueError(f"NodeType '{spec.fqn}' is already registered")

        self.node_types[spec.fqn] = spec
        self.node_logic_classes[spec.fqn] = logic_class

    def are_types_compatible(self, source_type: str, target_type: str) -> bool:
        source_spec = self.data_types.get(source_type)
        target_spec = self.data_types.get(target_type)
        if not source_spec or not target_spec:
            return False

        return DatatypeHelper.are_types_compatible(source_spec, target_spec)

    def get_logic_class(self, fqn: str) -> Type[BaseNode]:
        if not fqn in self.node_logic_classes:
            raise KeyError(f"No logic class is registered for {fqn}")
        
        return self.node_logic_classes[fqn]

    def get_datatype_spec(self, fqn: str) -> DataTypeSpec:
        if not fqn in self.data_types:
            raise KeyError(f"No DataTypeSpec is registered as {fqn}")
        
        return self.data_types[fqn]

    def get_datatype_by_annotation(self, py_type: type) -> Optional[DataTypeSpec]:
        if not py_type in self.data_types:
            raise KeyError(f"No DataTypeSpec is registered as {py_type}")
        
        return self.python_type_map.get(py_type)
