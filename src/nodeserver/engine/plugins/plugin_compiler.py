import importlib
from pathlib import Path
from typing import Any, Type

from nodeserver.engine.helpers.node_spec_builder import NodeSpecBuilder
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

    
    def compile_manifest(self, manifest: PluginManifest) -> ManifestPackage:
        package = ManifestPackage(
            version=manifest.version,
            package_id=manifest.package_id,
            data_types={},
            node_types={}
        )

        for plugin_dt_spec in manifest.data_types:
            full_class_path = self._resolve_import_path(manifest.package_id, plugin_dt_spec.class_path)
            module_path, class_name = full_class_path.rsplit(".", 1)
            
            module = importlib.import_module(module_path)
            cls_type = getattr(module, class_name)

            datatype_spec = DataTypeSpec.model_validate(
                plugin_dt_spec.model_dump(exclude={"class_path"})
            )

            self.registry.register_data_type(datatype_spec, cls_type)
            package.data_types[datatype_spec.fqn] = datatype_spec

        for relative_module_path in manifest.node_modules:
            full_module_path = self._resolve_import_path(manifest.package_id, relative_module_path)
            module = importlib.import_module(full_module_path)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if self._is_concrete_node_class(attr):
                    node_cls: Type[BaseNode] = attr
                    node_id = node_cls.__name__

                    node_type_spec: NodeTypeSpec = self.spec_builder.build_node_spec(
                        namespace=manifest.package_id,
                        id=node_id,
                        node_cls=node_cls
                    )

                    package.node_types[node_type_spec.fqn] = node_type_spec

        return package


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
