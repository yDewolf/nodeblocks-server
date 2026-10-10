from typing import Optional, Type

from nodeserver.engine.exceptions.plugin.plugin_internal_exceptions import PluginMissingNodeCacheEntry
from nodeserver.engine.exceptions.plugin.plugin_internal_exceptions import PluginMissingNodeCache
from nodeserver.engine.helpers.node_instance_factory import NodeInstanceFactory
from nodeserver.engine.helpers.node_spec_builder import NodeSpecBuilder
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.engine.plugins.protocols.plugin_specs import PluginDatatypeRef, PluginDatatypeSpec
from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.engine.protocols.node.node_instance import NodeInstance
from nodeserver.engine.protocols.providers.node_provider import INodeProvider
from nodeserver.protocols.manifest.base_manifest import split_fqn
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData
from nodeserver.protocols.manifest.package_manifest import ManifestPackage

class PluginNodeProvider(INodeProvider):
    _factory: NodeInstanceFactory
    plugin_manager: PluginManager

    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        self._factory = NodeInstanceFactory(plugin_manager.registry)

    # INodeProvider

    def extract_node_dependencies(self, node: BaseNode) -> set[tuple[str, str]]:
        dependencies: set[tuple[str, str]] = set()
        spec = self.plugin_manager.registry.get_node_type_spec(node.scene_data.nodetype_fqn)
        
        package = self.plugin_manager.ensure_package(spec.namespace)
        dependencies.add((package.package_id, package.version))
        
        datatypes = NodeSpecBuilder.extract_datatype_dependencies(spec)
        for dt_fqn in datatypes:
            dt_spec = self.plugin_manager.registry.get_datatype_spec(dt_fqn)
            dt_package = self.plugin_manager.ensure_package(dt_spec.namespace)
            dependencies.add((dt_package.package_id, dt_package.version))            
        
        return dependencies

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

        for datatype_fqn in required_datatypes:
            if registry.is_datatype_associated_python(datatype_fqn):
                continue
            
            datatype_ref = self.plugin_manager.ensure_plugin_datatype_ref(datatype_fqn)
            plugin_manifest = self.plugin_manager.ensure_plugin_manifest(datatype_ref.namespace)
            self._assign_datatype_python_type(plugin_manifest, datatype_ref, datatype_fqn)
            
    # FIXME: this shouldn't be done here
    def _assign_datatype_python_type(self, plugin_manifest: PluginManifest, datatype_ref: PluginDatatypeRef, datatype_fqn: str):
        compiler = self.plugin_manager.compiler
        registry = self.plugin_manager.registry
    
        cls_type = compiler.resolve_datatype_python_type(
            package_id=plugin_manifest.package_id,
            relative_class_path=datatype_ref.class_path
        )

        has_decorators = compiler._update_manifest_from_attr_decorators(cls_type, plugin_manifest, datatype_ref.class_path)
        aliases: list[type] = []
        if has_decorators:
            alias_paths: list[str] = []
            for dt_spec in plugin_manifest.data_types:
                if isinstance(dt_spec, PluginDatatypeSpec) and dt_spec.fqn == datatype_fqn:
                    alias_paths = dt_spec.alias_class_paths or []
                    break
            
            for class_path in alias_paths:
                alias = compiler.resolve_absolute_python_type(class_path)
                aliases.append(alias)

        registry.assign_datatype_python_type(datatype_fqn, cls_type, aliases)            
