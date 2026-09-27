import pytest

from pathlib import Path
import glob
import os

from nodeserver.engine.plugins.helpers.plugin_scanner import PluginScanner

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
