import sys
import pytest
from pathlib import Path
from unittest.mock import patch

from nodeserver.engine.plugins.plugin_compiler import PluginCompiler
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.plugins.plugin_node_provider import PluginNodeProvider
from nodeserver.engine.registry.type_registry import TypeRegistry

@pytest.fixture
def plugins_setup() -> tuple[Path, Path]:
    this_path = Path(__file__).parent
    tests_path = this_path.parent.parent.parent
    assert tests_path.name == "tests"
    root_path = tests_path.parent

    plugins_path = root_path / "test_plugins"
    plugins_path.mkdir(exist_ok=True)

    return root_path, plugins_path

@pytest.fixture()
def setup_sys_path(plugins_setup):
    root_path, _ = plugins_setup
    
    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))
    
    yield

    if str(root_path) in sys.path:
        sys.path.remove(str(root_path))

@pytest.fixture
def plugin_manager(default_registry, plugins_setup):
    _, plugins_path = plugins_setup

    dummy_registry = TypeRegistry.from_registry(default_registry)
    dummy_manager = PluginManager(
        registry=dummy_registry, 
        compiler=PluginCompiler(registry=dummy_registry, plugins_base_package="test_plugins")
    )
    dummy_manager.compile_plugins(plugins_path, save_to_disk=True)

    compiler = PluginCompiler(registry=default_registry, plugins_base_package="test_plugins")
    manager = PluginManager(registry=default_registry, compiler=compiler)
    manager.load_plugin_manifests(plugins_path)

    return manager

@pytest.fixture
def provider(plugin_manager):
    return PluginNodeProvider(plugin_manager=plugin_manager)



class TestLazyLoading:
    def test_lazy_load_node_success(self, provider, plugin_manager, setup_sys_path):
        """Garante que ao requisitar um nó não importado, ele é resolvido e instanciado."""
        registry = plugin_manager.registry
        node_fqn = "test_plugin:TestNode"
        
        # Garante o estado inicial limpo (nada foi importado ainda)
        assert node_fqn not in registry.node_logic_classes
        
        # Aciona o provedor
        node_instance, base_node = provider.create_node(node_fqn)
        
        # Asserções
        assert node_instance is not None
        assert base_node is not None
        assert base_node.__class__.__name__ == "TestNode"
        
        # Verifica se a atribuição atrasada funcionou no TypeRegistry
        assert node_fqn in registry.node_logic_classes
        assert registry.node_logic_classes[node_fqn] == base_node.__class__


    def test_lazy_load_datatypes_success(self, provider, plugin_manager, setup_sys_path):
        """Garante que pedir um nó de um plugin resolva seus Data Types no Registry também."""
        registry = plugin_manager.registry
        datatype_fqn = "test_plugin:test_datatype"
        
        # Estado inicial limpo
        assert not registry.is_datatype_associated_python(datatype_fqn)
        
        # Aciona a compilação e lazy load através da requisição de qualquer nó do plugin
        provider.create_node("test_plugin:TestNode")
        
        # Verifica se o DataType foi registrado e a classe Python resolvida
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

