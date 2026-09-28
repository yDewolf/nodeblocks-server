import importlib
from typing import Optional, Type

from nodeserver.engine.exceptions.plugin.plugin_internal_exceptions import PluginMissingNodeCacheEntry
from nodeserver.engine.exceptions.plugin.plugin_internal_exceptions import PluginMissingNodeCache
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

        if not node_fqn in self.plugin_manager.registry.node_types:
            raise KeyError(f"Tried to create a node that is not indexed {node_fqn}")

        package_id, _ = split_fqn(node_fqn)
        plugin_manifest = self.plugin_manager.ensure_plugin_manifest(package_id)

        if not plugin_manifest.nodes_cache:
            raise PluginMissingNodeCache(plugin_manifest.package_id)

        if not node_fqn in plugin_manifest.nodes_cache:
            raise PluginMissingNodeCacheEntry(node_fqn, plugin_manifest.package_id)
        
        cache_entry = plugin_manifest.nodes_cache[node_fqn]
        self._ensure_required_datatypes_loaded(cache_entry.required_datatypes)
        
        node_cls = self.plugin_manager.compiler.resolve_node_class(
            plugin_manifest.package_id,
            cache_entry.class_path
        )
        self.plugin_manager.registry.assign_node_logic_class(node_fqn, node_cls)


    def _ensure_required_datatypes_loaded(self, required_datatypes: list[str]) -> None:
        registry = self.plugin_manager.registry
        compiler = self.plugin_manager.compiler

        for datatype_fqn in required_datatypes:
            if registry.is_datatype_associated_python(datatype_fqn):
                continue
            
            datatype_ref = self.plugin_manager.ensure_plugin_datatype_ref(datatype_fqn)
            plugin_manifest = self.plugin_manager.ensure_plugin_manifest(datatype_ref.namespace)
            cls_type = compiler.resolve_datatype_python_type(
                package_id=plugin_manifest.package_id,
                relative_class_path=datatype_ref.class_path
            )
            registry.assign_datatype_python_type(datatype_fqn, cls_type)
