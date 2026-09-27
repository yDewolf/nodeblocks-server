import importlib
from pathlib import Path
from types import ModuleType
from typing import Any, Type

from nodeserver.engine.exceptions.plugin_exceptions import MissingNamespacePluginDataType, PluginDataTypeRefInCompileTime
from nodeserver.engine.helpers.node_spec_builder import NodeSpecBuilder
from nodeserver.engine.plugins.protocols.plugin_datatypes import PluginDatatypeRef, PluginDatatypeSpec
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec
from nodeserver.protocols.manifest.node.node_manifest import NodeTypeSpec
from nodeserver.protocols.manifest.package_manifest import ManifestPackage

class PluginCompiler:
    registry: TypeRegistry
    spec_builder: NodeSpecBuilder
    plugins_base_package: str

    def __init__(self, registry: TypeRegistry, plugins_base_package: str = "plugins"):
        self.plugins_base_package = plugins_base_package

        self.registry = registry
        self.spec_builder = NodeSpecBuilder(registry=self.registry)

    # Helper methods

    # TODO:
    # def compile_node_type_from_fqn(self, fqn: str):
    #     pass

    # def compile_data_type_from_fqn(self, fqn: str):
    #     pass

    # Compile Methods
    
    def compile_data_type_spec(
        self, 
        plugin_dt_spec: PluginDatatypeSpec, 
        assign_to_registry: bool = True
    ) -> DataTypeSpec:
        """
        Compiles a PluginDatatypeSpec into a DataTypeSpec
        """
        if not plugin_dt_spec.namespace:
            raise MissingNamespacePluginDataType(plugin_dt_spec.id, plugin_dt_spec.class_path)

        spec = DataTypeSpec(
            namespace=plugin_dt_spec.namespace, id=plugin_dt_spec.id,
            base_id=plugin_dt_spec.base_id,
            default_renderer=plugin_dt_spec.default_renderer,
            whitelist=plugin_dt_spec.whitelist
        )
        if assign_to_registry:
            self.registry.register_data_type(spec)

        return spec

    def compile_node_type(
        self,
        namespace: str,
        node_cls: Type[BaseNode],
        assign_logic_class: bool = True
    ) -> NodeTypeSpec:
        """
        Generates a NodeTypeSpec from a BaseNode class
        also registers it if assign_logic_class = true
        """
        node_type_spec: NodeTypeSpec = self.spec_builder.build_node_spec(
            namespace=namespace,
            id=node_cls.__name__,
            node_cls=node_cls
        )

        if assign_logic_class:
            if not self.registry.is_node_type_registered(node_type_spec.fqn):
                self.registry.register_node_type(node_type_spec, logic_class=node_cls)
            else:
                self.registry.assign_node_logic_class(node_type_spec.fqn, node_cls)

        return node_type_spec

    def compile_node_module(
        self,
        package_id: str,
        relative_module_path: str,
        assign_logic_classes: bool = True
    ) -> list[NodeTypeSpec]:
        """
        Imports a node module from a plugin and 
        compiles its logic classes (BaseNode)
        """

        module = self._import_python_module(package_id, relative_module_path)

        compiled_nodes: list[NodeTypeSpec] = []
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if self._is_concrete_node_class(attr):
                node_spec = self.compile_node_type(
                    namespace=package_id,
                    node_cls=attr,
                    assign_logic_class=assign_logic_classes
                )
                compiled_nodes.append(node_spec)

        return compiled_nodes


    def compile_manifest(
        self,
        manifest: PluginManifest,
        assign_to_registry: bool = True
    ) -> ManifestPackage:
        """
        Compiles a PluginManifest into a PackageManifest
        """
        package = ManifestPackage(
            version=manifest.version,
            package_id=manifest.package_id,
            data_types={},
            node_types={}
        )

        for plugin_dt_spec in manifest.data_types:
            if not isinstance(plugin_dt_spec, PluginDatatypeSpec):
                raise PluginDataTypeRefInCompileTime(plugin_dt_spec.fqn, manifest.package_id)

            datatype_spec = self.compile_data_type_spec(
                plugin_dt_spec=plugin_dt_spec,
                assign_to_registry=assign_to_registry
            )
            package.data_types[datatype_spec.fqn] = datatype_spec

        for relative_module in manifest.node_modules:
            node_specs = self.compile_node_module(
                package_id=manifest.package_id,
                relative_module_path=relative_module,
                assign_logic_classes=assign_to_registry
            )
            for node_spec in node_specs:
                package.node_types[node_spec.fqn] = node_spec

        return package

    # Import Resolve methods:

    def resolve_datatype_python_type(self, package_id: str, relative_class_path: str) -> Type:
        full_path = self._resolve_import_path(package_id, relative_class_path)
        module_path, class_name = full_path.rsplit(".", 1)

        try:
            module = importlib.import_module(module_path)
            return getattr(module, class_name)

        except (ImportError, AttributeError) as e:
            raise RuntimeError(f"Failed to import datatype python class {full_path}: {e}") from e
    
    # Utility:

    def _import_python_module(self, package_id: str, relative_module_path: str) -> ModuleType:
        full_path = self._resolve_import_path(package_id, relative_module_path)

        try:
            module = importlib.import_module(full_path)
            return module

        except (ImportError, AttributeError) as e:
            raise RuntimeError(f"Failed to import python type: {full_path}: {e}") from e


    @staticmethod
    def _is_concrete_node_class(attr: Any) -> bool:
        return (
            isinstance(attr, type)
            and issubclass(attr, BaseNode)
            and attr is not BaseNode
            and not getattr(attr, "__abstract__", False)
        )

    def _resolve_import_path(self, package_id: str, relative_path: str) -> str:
        if relative_path.startswith(self.plugins_base_package):
            return relative_path
        
        return f"{self.plugins_base_package}.{package_id}.{relative_path}"
