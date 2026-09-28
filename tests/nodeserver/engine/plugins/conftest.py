
from pathlib import Path
import sys

import pytest

from nodeserver.engine.plugins.plugin_compiler import PluginCompiler
from nodeserver.engine.plugins.plugin_manager import PluginManager
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

@pytest.fixture(autouse=True)
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
