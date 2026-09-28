from typing import Optional
from pathlib import Path
import pytest

from nodeserver.engine.engine_version import CURRENT_ENGINE_VERSION
from nodeserver.engine.plugins.plugin import Plugin
from nodeserver.engine.plugins.plugin_api_version import CURRENT_PLUGIN_API_VERSION
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.engine.exceptions.plugin.plugin_internal_exceptions import PluginMissingSourceHash, PluginNotLoadedError
from nodeserver.engine.plugins.helpers.plugin_manifest_helper import PluginManifestHelper
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.engine.plugins.protocols.plugin_specs import PluginDatatypeRef
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.manifest.package_manifest import ManifestPackage


@pytest.fixture
def dummy_plugin_manager():
    return PluginManager(
        registry=TypeRegistry(),
    )


def create_manifest(
    package_id: str,
    version: str = "1.0.0",
    dependencies: Optional[dict] = None,
    source_hash: str = "hash_123",
    data_types: Optional[list] = None,
) -> PluginManifest:
    return PluginManifest(
        engine_version=CURRENT_ENGINE_VERSION,
        plugin_api_version=CURRENT_PLUGIN_API_VERSION,
        package_id=package_id,
        plugin_version=version,
        dependencies=dependencies or {},
        source_hash=source_hash,
        data_types=data_types or [],
    )

def create_package(package_id: str, version: str = "1.0.0") -> ManifestPackage:
    return ManifestPackage(
        package_id=package_id,
        version=version,
        data_types={},
        node_types={},
    )


class TestResolvePluginLoadOrder:
    def test_plugin_topology_ordering(self, dummy_plugin_manager):
        path = Path("/dummy/path")
        manifest_a = create_manifest("plugin_a")
        manifest_b = create_manifest("plugin_b", dependencies={"plugin_a": ">=1.0.0"})
        manifest_c = create_manifest("plugin_c", dependencies={"plugin_b": ">=1.0.0"})

        input_list = [
            (manifest_c, path / "c"),
            (manifest_a, path / "a"),
            (manifest_b, path / "b"),
        ]

        ordered = dummy_plugin_manager.resolve_plugin_load_order(input_list)
        ordered_ids = [m[0].package_id for m in ordered]

        assert ordered_ids == ["plugin_a", "plugin_b", "plugin_c"]

    def test_fail_on_duplicate_plugin(self, dummy_plugin_manager):
        path = Path("/dummy/path")
        manifest_a1 = create_manifest("plugin_a")
        manifest_a2 = create_manifest("plugin_a")

        input_list = [(manifest_a1, path), (manifest_a2, path)]

        with pytest.raises(Exception):
            dummy_plugin_manager.resolve_plugin_load_order(input_list)

    def test_fail_on_missing_dependency(self, dummy_plugin_manager):
        path = Path("/dummy/path")
        manifest_a = create_manifest("plugin_a", dependencies={"plugin_inexistente": "1.0.0"})

        input_list = [(manifest_a, path)]

        with pytest.raises(Exception):
            dummy_plugin_manager.resolve_plugin_load_order(input_list)

    def test_fail_on_circular_dependency(self, dummy_plugin_manager):
        path = Path("/dummy/path")
        manifest_a = create_manifest("plugin_a", dependencies={"plugin_b": "1.0.0"})
        manifest_b = create_manifest("plugin_b", dependencies={"plugin_a": "1.0.0"})

        input_list = [(manifest_a, path), (manifest_b, path)]

        with pytest.raises(Exception):
            dummy_plugin_manager.resolve_plugin_load_order(input_list)


class TestRegistrationAndIndexing:
    def test_register_compiled_package(self, dummy_plugin_manager):
        package = create_package("test_pkg")

        dummy_plugin_manager.register_compiled_package(package)

        assert dummy_plugin_manager.is_package_loaded("test_pkg") is True
        assert dummy_plugin_manager.get_loaded_package("test_pkg") == package

    def test_index_plugin_e_datatype_ref(self, dummy_plugin_manager):
        dt_ref = PluginDatatypeRef(
            namespace="test_pkg",
            id="my_datatype",
            class_path="datatypes.MyDatatype",
        )
        manifest = create_manifest("test_pkg", data_types=[dt_ref])

        dummy_plugin_manager.index_plugin(manifest)

        assert dummy_plugin_manager.get_plugin_manifest("test_pkg") == manifest
        assert dummy_plugin_manager.get_plugin_datatype_ref(dt_ref.fqn) == dt_ref


class TestEnsuresAndGetters:
    def test_ensure_plugin_manifest_success(self, dummy_plugin_manager):
        manifest = create_manifest("pkg_1")
        dummy_plugin_manager.index_plugin(manifest)

        result = dummy_plugin_manager.ensure_plugin_manifest("pkg_1")
        assert result == manifest

    def test_ensure_plugin_manifest_error(self, dummy_plugin_manager):
        with pytest.raises(PluginNotLoadedError):
            dummy_plugin_manager.ensure_plugin_manifest("pkg_desconhecido")

    def test_ensure_plugin_datatype_ref_success(self, dummy_plugin_manager):
        dt_ref = PluginDatatypeRef(
            namespace="pkg",
            id="type_a",
            class_path="types.TypeA",
        )
        manifest = create_manifest("pkg", data_types=[dt_ref])
        dummy_plugin_manager.index_plugin(manifest)

        assert dummy_plugin_manager.ensure_plugin_datatype_ref("pkg:type_a") == dt_ref

    def test_ensure_plugin_datatype_ref_error(self, dummy_plugin_manager):
        with pytest.raises(KeyError):
            dummy_plugin_manager.ensure_plugin_datatype_ref("pkg:inexistente")

    def test_get_all_loaded_packages_returns_isolated_copy(self, dummy_plugin_manager):
        package = create_package("pkg_1")
        dummy_plugin_manager.register_compiled_package(package)

        loaded_copy = dummy_plugin_manager.get_all_loaded_packages()
        assert loaded_copy == {"pkg_1": package}

        loaded_copy.clear()
        assert dummy_plugin_manager.get_loaded_package("pkg_1") == package


class TestPluginDiskOperations:
    def test_load_plugin_manifests(self, dummy_plugin_manager, tmp_path):
        plugin_folder = PluginManifestHelper.make_plugin_folder_structure(tmp_path, "test_0")
        manifests_folder = PluginManifestHelper.get_plugin_cache_folder(plugin_folder)
        manifests_folder.mkdir()

        package = create_package("plugin_a")
        manifest = create_manifest("plugin_a")

        PluginManifestHelper.save_package_manifest(package, manifests_folder)
        PluginManifestHelper.save_plugin_manifest(manifest, manifests_folder)

        result = dummy_plugin_manager.load_plugin_manifests(plugin_folder)

        assert "plugin_a" in result
        assert dummy_plugin_manager.get_plugin_manifest("plugin_a") == manifest
        assert dummy_plugin_manager.is_plugin_loaded("plugin_a") is True

    def test_load_or_compile_plugins_compiles_and_saves_cache(self, dummy_plugin_manager, tmp_path):
        source_dir = tmp_path / "plugins_src"
        source_dir.mkdir(exist_ok=True)
        plugin_dir = PluginManifestHelper.make_plugin_folder_structure(source_dir, "my_plugin")

        plugin_file = plugin_dir / "plugin.py"
        plugin_file.write_text(
            f"from {PluginManifest.__module__} import {PluginManifest.__name__}\n"
            f"from {Plugin.__module__} import {Plugin.__name__}\n"
            f"class TestPlugin({Plugin.__name__}): manifest = PluginManifest(package_id='my_plugin', plugin_version='1.0.0', plugin_api_version='{CURRENT_PLUGIN_API_VERSION}', engine_version='{CURRENT_ENGINE_VERSION}')\n"
        )

        dummy_plugin_manager.load_or_compile_plugins(source_dir)
        
        assert dummy_plugin_manager.get_plugin_manifest("my_plugin") is not None
        
        cache_list_file = source_dir / ".plugin_list.json"
        assert cache_list_file.exists()

    def test_load_or_compile_plugins_missing_hash_exception(self, dummy_plugin_manager, tmp_path):
        source_dir = tmp_path / "plugins_src"
        plugin_dir = source_dir / "unhashed_plugin"
        plugin_dir.mkdir(parents=True)

        manifest = create_manifest("unhashed_plugin", source_hash="")
        
        dummy_plugin_manager.scanner.discover_plugins = lambda path: [(manifest, plugin_dir / "plugin.py")]

        with pytest.raises(PluginMissingSourceHash):
            dummy_plugin_manager.load_or_compile_plugins(source_dir)
