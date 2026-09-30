import pytest
from unittest.mock import patch

from nodeserver.engine.plugins.plugin_node_provider import PluginNodeProvider

@pytest.fixture
def provider(plugin_manager):
    return PluginNodeProvider(plugin_manager=plugin_manager)

class TestLazyLoading:
    def test_lazy_load_node_success(self, provider, plugin_manager, setup_sys_path):
        registry = plugin_manager.registry
        node_fqn = "test_plugin:TestNode"
        
        assert node_fqn not in registry.node_logic_classes
        node_instance, base_node = provider.create_node(node_fqn)

        assert node_instance is not None
        assert base_node is not None
        assert base_node.__class__.__name__ == "TestNode"
        
        assert node_fqn in registry.node_logic_classes
        assert registry.node_logic_classes[node_fqn] == base_node.__class__


    def test_lazy_load_datatypes_success(self, provider, plugin_manager, setup_sys_path):
        registry = plugin_manager.registry
        datatype_fqn = "test_plugin:test_datatype"
        
        assert not registry.is_datatype_associated_python(datatype_fqn)
        
        provider.create_node("test_plugin:TestNode")
        
        resolved_class = registry.get_datatype_python_type(datatype_fqn)
        assert resolved_class is not None
        assert resolved_class.__name__ == "TestDatatype"


    def test_lazy_load_fast_path_cache(self, provider, plugin_manager, setup_sys_path):
        node_fqn = "test_plugin:TestNode"
        provider.create_node(node_fqn)
        
        compiler = plugin_manager.compiler
        
        with patch.object(compiler, 'compile_node_module') as mock_compile:
            provider.create_node(node_fqn)
            
            mock_compile.assert_not_called()


    def test_lazy_load_node_not_found(self, provider, setup_sys_path):
        node_fqn = "test_plugin:UnknownNode"
        
        with pytest.raises(KeyError) as exc_info:
            provider.create_node(node_fqn)
