from typing import Optional, Self, Type

from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.protocols.helpers.datatype_helper import DatatypeHelper
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec
from nodeserver.protocols.manifest.node.node_manifest import NodeTypeSpec

class TypeSpecRegistry:
    # type_id -> spec
    node_types: dict[str, NodeTypeSpec]

    # type_id -> spec
    data_types: dict[str, DataTypeSpec]

    def __init__(self):
        self.reset()

    def reset(self):
        self.data_types = {}
        self.node_types = {}

    def copy_from_registry(self, registry: 'TypeSpecRegistry'):
        self.data_types = registry.data_types.copy()
        self.node_types = registry.node_types.copy()

    @classmethod
    def from_registry(cls, registry: 'TypeSpecRegistry') -> Self:
        new_registry = cls()
        new_registry.copy_from_registry(registry)

        return new_registry


    def register_data_type(self, spec: DataTypeSpec):
        if spec.fqn in self.data_types:
            raise ValueError(f"DataType '{spec.fqn}' is already registered")

        self.data_types[spec.fqn] = spec
    
    def register_node_type(self, spec: NodeTypeSpec):
        if spec.fqn in self.node_types:
            raise ValueError(f"NodeType '{spec.fqn}' is already registered")

        self.node_types[spec.fqn] = spec


    def are_types_compatible(self, source_type: str, target_type: str) -> bool:
        source_spec = self.data_types.get(source_type)
        target_spec = self.data_types.get(target_type)
        if not source_spec or not target_spec:
            return False

        return DatatypeHelper.are_types_compatible(source_spec, target_spec)

    # Boolean checks:

    def is_node_type_registered(self, nodetype_fqn: str) -> bool:
        return nodetype_fqn in self.node_types

    # Getters:
    
    def get_node_type_spec(self, fqn: str) -> NodeTypeSpec:
        if not self.is_node_type_registered(fqn):
            raise KeyError(f"No NodeTypeSpec is registerd as {fqn}")
        
        return self.node_types[fqn]

    def get_datatype_spec(self, fqn: str) -> DataTypeSpec:
        if not fqn in self.data_types:
            raise KeyError(f"No DataTypeSpec is registered as {fqn}")
        
        return self.data_types[fqn]

class TypeRegistry(TypeSpecRegistry):
    node_logic_classes: dict[str, Type[BaseNode]]
    python_type_map: dict[type, DataTypeSpec]
    _fqn_to_python_type: dict[str, type]

    def reset(self):
        super().reset()
        self.node_logic_classes = {}
        self.python_type_map = {}
        self._fqn_to_python_type = {}

    def copy_from_registry(self, registry: 'TypeRegistry'):
        super().copy_from_registry(registry)
        self.node_logic_classes = registry.node_logic_classes.copy()
        self.python_type_map = registry.python_type_map.copy()
        self._fqn_to_python_type = registry._fqn_to_python_type.copy()

    def register_data_type(self, spec: DataTypeSpec, python_type: Optional[type] = None):
        super().register_data_type(spec)

        if python_type is not None:
            self.assign_datatype_python_type(spec.fqn, python_type)
    
    def register_node_type(self, spec: NodeTypeSpec, logic_class: Optional[Type[BaseNode]] = None):
        super().register_node_type(spec)

        if not logic_class is None:
            self.assign_node_logic_class(spec.fqn, logic_class)

    # Late Assignment methods

    def assign_node_logic_class(self, node_fqn: str, logic_class: Type[BaseNode]):
        if node_fqn in self.node_logic_classes:
            raise KeyError(f"{node_fqn} already has a logic class assigned ({self.node_logic_classes[node_fqn]})")

        self.node_logic_classes[node_fqn] = logic_class

    def assign_datatype_python_type(self, datatype_fqn: str, python_type: Type):
        if datatype_fqn not in self.data_types:
            raise KeyError(f"DataTypeSpec {datatype_fqn} must be registered before assigning a Python type")

        if datatype_fqn in self._fqn_to_python_type:
            existing_type = self._fqn_to_python_type[datatype_fqn]
            raise KeyError(f"{datatype_fqn} is already assigned to a Python type {existing_type}")

        self._fqn_to_python_type[datatype_fqn] = python_type
        self.python_type_map[python_type] = self.data_types[datatype_fqn]

    # Boolean checks

    def is_datatype_associated_python(self, datatype_fqn: str) -> bool:
        return datatype_fqn in self._fqn_to_python_type

    # Getters

    def get_logic_class(self, fqn: str) -> Type[BaseNode]:
        if not fqn in self.node_logic_classes:
            raise KeyError(f"No logic class is registered for {fqn}")
        
        return self.node_logic_classes[fqn]

    def get_datatype_by_annotation(self, py_type: type) -> DataTypeSpec:
        if not py_type in self.python_type_map:
            raise KeyError(f"No DataTypeSpec is registered as {py_type}")
        
        return self.python_type_map[py_type]

    def get_datatype_python_type(self, datatype_fqn: str) -> Optional[Type]:
        if not self.is_datatype_associated_python(datatype_fqn):
            raise KeyError(f"No python type is assigned to {datatype_fqn}")
        
        return self._fqn_to_python_type.get(datatype_fqn)
