import importlib
from typing import Optional, Type

from nodeserver.engine.helpers.node_instance_factory import NodeInstanceFactory
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.engine.protocols.node.node_instance import NodeInstance
from nodeserver.engine.protocols.node_provider import INodeProvider
from nodeserver.protocols.manifest.base_manifest import split_fqn
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData

class PluginNodeProvider(INodeProvider):
    _factory: NodeInstanceFactory

    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        self._factory = NodeInstanceFactory(plugin_manager.registry)

    # INodeProvider

    def create_node(
        self, 
        node_fqn: str, 
        node_scene_data: Optional[NodeSceneData] = None
    ) -> tuple[NodeInstance, BaseNode]:
        self._lazy_assign_node_class(node_fqn)
        return self._factory.create(node_fqn, node_scene_data)

    # Lazy Assignment

    def _lazy_assign_node_class(self, node_fqn: str) -> None:
        registry = self.plugin_manager.registry
        if node_fqn in registry.node_logic_classes:
            return

        package_id, _ = split_fqn(node_fqn)
        plugin_manifest = self.plugin_manager.ensure_plugin_manifest(package_id)
        self._ensure_plugin_datatypes_loaded(plugin_manifest)

        for relative_module in plugin_manifest.node_modules:
            self.plugin_manager.compiler.compile_node_module(
                package_id=package_id,
                relative_module_path=relative_module,
                assign_logic_classes=True
            )
            if node_fqn in registry.node_logic_classes:
                return

        if node_fqn not in registry.node_logic_classes:
            raise RuntimeError(f"Não foi possível encontrar a classe do nó '{node_fqn}' nos módulos do plugin.")

    def _ensure_plugin_datatypes_loaded(self, plugin_manifest: PluginManifest) -> None:
        registry = self.plugin_manager.registry
        compiler = self.plugin_manager.compiler

        for dt_spec in plugin_manifest.data_types:
            if not registry.is_datatype_associated_python(dt_spec.fqn):
                cls_type = compiler.resolve_datatype_python_type(
                    package_id=plugin_manifest.package_id,
                    relative_class_path=dt_spec.class_path
                )
                registry.assign_datatype_python_type(dt_spec.fqn, cls_type)
