
from pathlib import Path
import sys

import pytest

from nodeblocks.engine.engine_env import ENGINE_ENV
from nodeblocks.engine.plugins.plugin_compiler import PluginCompiler
from nodeblocks.engine.plugins.plugin_manager import PluginManager
from nodeblocks.engine.registry.type_registry import TypeRegistry


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
    root_path, plugins_path = plugins_setup
    
    if str(plugins_path) not in sys.path:
        sys.path.insert(0, str(plugins_path))

    if str(ENGINE_ENV.core_plugins_folder) not in sys.path:
        sys.path.insert(0, str(ENGINE_ENV.core_plugins_folder))
    
    yield

    if str(plugins_path) in sys.path:
        sys.path.remove(str(plugins_path))

    if str(ENGINE_ENV.core_plugins_folder) in sys.path:
        sys.path.remove(str(ENGINE_ENV.core_plugins_folder))

@pytest.fixture
def plugin_manager(plugins_setup):
    _, plugins_path = plugins_setup

    dummy_registry = TypeRegistry()
    dummy_manager = PluginManager(
        registry=dummy_registry, 
        compiler=PluginCompiler(registry=dummy_registry, plugins_base_package="test_plugins")
    )
    plugin_folders = [plugins_path, ENGINE_ENV.core_plugins_folder]
    dummy_manager.compile_plugins(plugin_folders, save_plugin_cache=True)

    registry = TypeRegistry()
    compiler = PluginCompiler(registry=registry, plugins_base_package="test_plugins")
    manager = PluginManager(registry=registry, compiler=compiler)
    manager.load_plugin_manifests(plugin_folders)

    return manager
