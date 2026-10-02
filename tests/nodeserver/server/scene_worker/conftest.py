import pytest
from multiprocessing import Queue
from pathlib import Path

from nodeserver.engine.engine_version import CURRENT_ENGINE_VERSION
from nodeserver.engine.plugins.api.plugin_api_version import CURRENT_PLUGIN_API_VERSION
from nodeserver.engine.plugins.protocols.plugin_manifest import PluginManifest
from nodeserver.engine.workers.scene_worker import SceneWorker
from nodeserver.protocols.manifest.node.node_graph import SceneData


@pytest.fixture
def worker(tmp_path: Path) -> SceneWorker:
    cmd_queue: Queue = Queue()
    evt_queue: Queue = Queue()
    plugins_folder = tmp_path / "plugins"
    plugins_folder.mkdir(parents=True, exist_ok=True)

    worker = SceneWorker(plugins_folder, cmd_queue, evt_queue)
    test_plugin = PluginManifest(
        source_hash="test", package_id="test_package", 
        engine_version=CURRENT_ENGINE_VERSION, plugin_api_version=CURRENT_PLUGIN_API_VERSION,
        plugin_version="0.0.0"
    )
    worker.plugin_manager.index_plugin(test_plugin)
    return worker


@pytest.fixture
def scene_data() -> SceneData:
    return SceneData(
        package_id="test_package",
        package_version="0.0.0",
        nodes={},
        connections={}
    )
