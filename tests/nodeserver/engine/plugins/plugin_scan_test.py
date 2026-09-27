import pytest

from pathlib import Path

from nodeserver.engine.plugins.helpers.plugin_scanner import PluginScanner
from nodeserver.engine.plugins.plugin_compiler import PluginCompiler
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.manifest.package_manifest import ManifestPackage

@pytest.fixture
def plugins_setup() -> tuple[Path, Path]:
    this_path = Path(__file__).parent
    tests_path = this_path.parent.parent.parent
    assert tests_path.name == "tests"
    root_path = tests_path.parent

    plugins_path = root_path / "test_plugins"
    # if plugins_path.exists():
    #     files = glob.glob(str(plugins_path))
    #     for f in files:
    #         os.remove(f)
    
    plugins_path.mkdir(exist_ok=True)

    return root_path, plugins_path


class TestPluginScan:
    def test_plugin_scan(self, plugins_setup):
        root_path, plugins_path = plugins_setup
        scanner = PluginScanner(plugins_path)
        
        discovered_plugins = scanner.discover_plugins()
        assert len(discovered_plugins) >= 1

#     def test_plugin_scan(self, plugins_setup):
#         root_path, plugins_path = plugins_setup

#         test_plugin_path = plugins_path / "test_plugin"
#         test_plugin_path.mkdir(exist_ok=True)

#         plugin_file = test_plugin_path / "plugin.py"
#         plugin_file.write_text(
# """
# from nodeserver.engine.plugins.plugin import Plugin
# from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest

# class TestPlugin(Plugin):
#     manifest = PluginManifest(
#         package_id="test.package"
#         version="0.0.1"

#         node_modules=[

#         ]
#     )
# """
#         )


@pytest.fixture
def compiler(plugins_setup, default_registry):
    root_path, plugins_path = plugins_setup
    compiler = PluginCompiler(default_registry, plugins_path.name)
    return compiler    

class TestPluginCompile:
    def test_plugin_compile(self, plugins_setup, compiler):
        root_path, plugins_path = plugins_setup
        scanner = PluginScanner(plugins_path)
        discovered_plugins = scanner.discover_plugins()
        
        assert len(discovered_plugins) >= 1

        compiled_manifests: list[ManifestPackage] = []
        for plugin_manifest in discovered_plugins:
            manifest = compiler.compile_manifest(plugin_manifest)
            compiled_manifests.append(manifest)

        assert len(compiled_manifests) == len(discovered_plugins)
