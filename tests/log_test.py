from pathlib import Path
import sys
from typing import Any

from nodeserver.engine.plugins.plugin_compiler import PluginCompiler
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers
from nodeserver.protocols.helpers.datatype_helper import DatatypeHelper

import logging.config
logging.config.fileConfig("logging.conf")


if __name__ == "__main__":
    root_path = Path(__file__).parent.parent
    if str() not in sys.path:
        sys.path.insert(0, str(root_path))

    plugins_path = root_path / "test_plugins"

    reg = TypeRegistry()
    namespace = "core"

    reg.register_data_type(
        DatatypeHelper.create_spec(namespace, "string", base_id=DefaultDataTypes.TEXT, renderer=DefaultRenderers.TEXT),
        python_type=str
    )
    reg.register_data_type(
        DatatypeHelper.create_spec(namespace, "int", base_id=DefaultDataTypes.INT, renderer=DefaultRenderers.SCALAR),
        python_type=int
    )
    reg.register_data_type(
        DatatypeHelper.create_spec(namespace, "float", base_id=DefaultDataTypes.FLOAT, renderer=DefaultRenderers.SCALAR),
        python_type=float
    )
    reg.register_data_type(
        DatatypeHelper.create_spec(namespace, "unknown", base_id=DefaultDataTypes.UNKNOWN, renderer=DefaultRenderers.NOT_IMPLEMENTED),
        python_type=type[Any]
    )

    dummy_registry = TypeRegistry.from_registry(reg)
    dummy_manager = PluginManager(
        registry=dummy_registry, 
        compiler=PluginCompiler(registry=dummy_registry, plugins_base_package="test_plugins")
    )
    dummy_manager.load_or_compile_plugins(plugins_path, save_to_disk=True)

    # compiler = PluginCompiler(registry=reg, plugins_base_package="test_plugins")
    # manager = PluginManager(registry=reg, compiler=compiler)
    # manager.load_plugin_manifests(plugins_path)


    if str(root_path) in sys.path:
        sys.path.remove(str(root_path))
