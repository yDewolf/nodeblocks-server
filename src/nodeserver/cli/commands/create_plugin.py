
from argparse import _SubParsersAction, ArgumentParser, Namespace
from pathlib import Path
import sys

from nodeserver.cli.commands.base_command import CLICommand
from nodeserver.engine.engine_version import CURRENT_ENGINE_VERSION
from nodeserver.engine.plugins.api import CURRENT_PLUGIN_API_VERSION, PluginDatatype, Plugin
from nodeserver.engine.plugins.api.decorators import plugin_node, plugin_datatype
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.engine.protocols.node.logic_nodes import BaseNode, NodeInputs, NodeOutputs
from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers


class CreatePluginCMD(CLICommand):
    @classmethod
    def on_register_command(cls, subparsers: _SubParsersAction[ArgumentParser]):
        parser = subparsers.add_parser(
            "create:plugin",
            description="Generates an Example Plugin Structure."
        )
        parser.add_argument(
            "path",
            type=Path,
            nargs="?",
            default=Path("."),
            help="Where the plugin folder should be created. Final plugin path will be: provided_path/your_package_id/plugin.py",
        )
        parser.add_argument(
            "--id",
            dest="package_id",
            type=str,
            default=None,
            help="Package id of your plugin (example: my_package, com.myname.mypackage). If omitted, will use folder name.",
        )
        return parser

    @classmethod
    def run(cls, args: Namespace):
        target_dir = Path(args.path)
        package_id: str = args.package_id

        target_dir = target_dir.resolve()
        pkg_id = package_id or target_dir.name.lower().replace("-", "_").replace(" ", "_")
        
        words = pkg_id.replace("_", " ").title().split()
        class_name = "".join(words)
        plugin_name = " ".join(words)

        plugin_dir = target_dir / pkg_id
        if plugin_dir.exists() and any(plugin_dir.iterdir()):
            print(f"Error: Folder '{plugin_dir}' already exists and is not empty", file=sys.stderr)
            sys.exit(1)

        nodes_dir = plugin_dir / "nodes"
        datatypes_dir = plugin_dir / "datatypes"
        
        nodes_dir.mkdir(parents=True, exist_ok=True)
        datatypes_dir.mkdir(parents=True, exist_ok=True)

        plugin_file = plugin_dir / "plugin.py"
        plugin_content = build_plugin_py_template(class_name, pkg_id, plugin_name)
        plugin_file.write_text(plugin_content, encoding="utf-8")
        
        (nodes_dir / "example_node.py").write_text(TEMPLATE_EXAMPLE_NODE, encoding="utf-8")
        (datatypes_dir / "example_type.py").write_text(TEMPLATE_EXAMPLE_DATATYPE, encoding="utf-8")

        print(f"\nGenerated plugin files at {plugin_dir}:")
        print("  ├── plugin.py")
        print("  ├── nodes/")
        print("  │   └── example_node.py")
        print("  └── datatypes/")
        print("      └── example_type.py\n")

        print(f"You must keep 'plugin.py' directly inside of '{pkg_id}/'")
        print("Otherwise your plugin might not be identified.")
        print("As long as datatypes and nodes are decorated")
        print("they might be anywhere inside your plugin folder")


def build_plugin_py_template(class_name: str, package_id: str, plugin_name: str) -> str:
    return f"""from {PluginManifest.__module__} import {PluginManifest.__name__}
from {Plugin.__module__} import {Plugin.__name__}


class {class_name}Plugin({Plugin.__name__}):
    manifest = {PluginManifest.__name__}(
        package_id="{package_id}",
        plugin_version="0.1.0",
        description="Description for {plugin_name}",
        authors=["you"],
        engine_version=f">={CURRENT_ENGINE_VERSION}", # Current Engine Version
        plugin_api_version=f">={CURRENT_PLUGIN_API_VERSION}", # Current Plugin API Version
        dependencies={{}},
    )
"""

TEMPLATE_EXAMPLE_NODE = f"""from {plugin_node.__module__} import {plugin_node.__name__}
from {BaseNode.__module__} import {BaseNode.__name__}, {NodeInputs.__name__}, {NodeOutputs.__name__}


class ExampleNodeInput({NodeInputs.__name__}):
    in_0: float


class ExampleNodeOutput({NodeOutputs.__name__}):
    out_0: float


@{plugin_node.__name__}()
class ExampleNode({BaseNode.__name__}[ExampleNodeInput, ExampleNodeOutput]):
    InputModel = ExampleNodeInput
    OutputModel = ExampleNodeOutput

    def forward(self, inputs: ExampleNodeInput) -> ExampleNodeOutput:
        return ExampleNodeOutput(
            out_0=inputs.in_0 + 1,
        )
"""

TEMPLATE_EXAMPLE_DATATYPE = f"""from {plugin_datatype.__module__} import {plugin_datatype.__name__}
from {PluginDatatype.__module__} import {PluginDatatype.__name__}
from {DefaultDataTypes.__module__} import {DefaultDataTypes.__name__}, {DefaultRenderers.__name__}


@{plugin_datatype.__name__}(
    id="example_datatype",
    base_id={DefaultDataTypes.__name__}.CUSTOM,
    default_renderer={DefaultRenderers.__name__}.NOT_IMPLEMENTED,
)
class ExampleDataType({PluginDatatype.__name__}):
    \"\"\"Implement your datatype class here\"\"\"

    def serialize(self):
        \"\"\"
        Serialization method for your custom datatype.
        Must return a json compatible type.
        \"\"\"
        pass
"""