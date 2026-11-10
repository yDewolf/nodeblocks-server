from typing import Optional

import pytest
from multiprocessing import Queue
from pathlib import Path

from nodeblocks.engine.engine_version import CURRENT_ENGINE_VERSION
from nodeblocks.engine.plugins.api.plugin_api_version import CURRENT_PLUGIN_API_VERSION
from nodeblocks.engine.plugins.plugin_manager import PluginManager
from nodeblocks.engine.plugins.plugin_node_provider import PluginNodeProvider
from nodeblocks.engine.plugins.protocols.plugin_manifest import EnginePluginManifest
from nodeblocks.engine.protocols.node.logic_nodes import BaseNode, NodeInputs, NodeOutputs
from nodeblocks.engine.protocols.node.node_scene import NodeScene
from nodeblocks.engine.providers.base_scene_providers import NoSceneArtifactProvider, NoSceneDataProvider, NoSceneStateProvider
from nodeblocks.engine.providers.file_artifact_provider import FileArtifactProvider
from nodeblocks.engine.providers.file_scene_provider import FileSceneDataProvider, FileSceneStateProvider
from nodeblocks.engine.runtime.job_runtime_context import SceneSuperContext
from nodeblocks.engine.workers.scene.scene_worker import SceneWorker
from nodeblocks.engine.workers.scene.scene_worker_cmd_handler import SceneWorkerCommandHandler
from nodeblocks.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers
from nodeblocks.protocols.manifest.node.datatypes import DataTypeSpec
from nodeblocks.protocols.manifest.node.node_graph import ConnectionSceneData, NodeSceneData, SceneData
from nodeblocks.protocols.manifest.node.node_manifest import NodeSlotSpec, NodeTypeSpec
from nodeblocks.protocols.manifest.package_manifest import ManifestPackage

class SceneWorkerNodeIn(NodeInputs):
    in_0: Optional[int] = 0

class SceneWorkerNodeOut(NodeOutputs):
    out_0: int

class SceneWorkerNode(BaseNode[SceneWorkerNodeIn, SceneWorkerNodeOut]):
    InputModel = SceneWorkerNodeIn
    OutputModel = SceneWorkerNodeOut

    def forward(self, inputs: SceneWorkerNodeIn) -> SceneWorkerNodeOut:
        return SceneWorkerNodeOut(
            out_0=(inputs.in_0 or 0) + 1
        )


@pytest.fixture
def packages():
    package_id: str = "test_package"
    test_plugin = EnginePluginManifest(
        source_hash="test", package_id=package_id, 
        engine_version=CURRENT_ENGINE_VERSION, plugin_api_version=CURRENT_PLUGIN_API_VERSION,
        plugin_version="0.0.0"
    )
    test_package = ManifestPackage(
        version="0.0.0", package_id=package_id,
        data_types={
            f"{package_id}:int": DataTypeSpec(namespace=package_id, id="int", base_id=DefaultDataTypes.INT, default_renderer=DefaultRenderers.SCALAR, whitelist=[f"{package_id}:int"])
        },
        node_types={
            f"{package_id}:node": NodeTypeSpec(
                namespace=package_id, id="node", parameters={}, 
                slots={
                    "in_0": NodeSlotSpec(datatype_fqn=f"{package_id}:int", is_input=True),
                    "out_0": NodeSlotSpec(datatype_fqn=f"{package_id}:int", is_input=True),
                }
            )
        }
    )
    return test_plugin, test_package, package_id

@pytest.fixture
def populated_scene(packages):
    test_plugin, test_package, package_id = packages
    return SceneData(
        dependencies={
            package_id: "0.0.0"
        },
        nodes={
            "node_0": NodeSceneData(uid="node_0", nodetype_fqn=f"{package_id}:node"),
            "node_1": NodeSceneData(uid="node_1", nodetype_fqn=f"{package_id}:node"),
        },
        connections={
            "conn_0": ConnectionSceneData.from_ids(
                from_node_id="node_0", from_slot_id="out_0",
                to_node_id="node_1", to_slot_id="in_0"
            )
        }
    )

@pytest.fixture
def worker(tmp_path: Path, packages) -> SceneWorker:
    plugins_folder = tmp_path / "plugins"
    plugins_folder.mkdir(parents=True, exist_ok=True)

    scene_id = "test_scene"

    plugin_manager = PluginManager.new()

    data_provider = NoSceneDataProvider()
    state_provider = NoSceneStateProvider(scene_id)
    worker = SceneWorker(
        scene_id, plugins_folder, plugins_folder,
        data_provider,
        state_provider,
        NoSceneArtifactProvider(scene_id),
        plugin_manager=plugin_manager
    )
    command_handler = SceneWorkerCommandHandler(worker, Queue(), Queue())
    worker.set_command_handler(command_handler)

    test_plugin, test_package, package_id = packages
    worker.plugin_manager.register_compiled_package(test_package)
    worker.plugin_manager.index_plugin(test_plugin)

    worker.plugin_manager.registry.assign_datatype_python_type(f"{package_id}:int", int)
    worker.plugin_manager.registry.assign_node_logic_class(f"{package_id}:node", SceneWorkerNode)

    node_scene = NodeScene(
        plugin_manager.registry, 
        node_provider=worker.node_provider,
        scene_data_provider=data_provider,
        scene_state_provider=state_provider,
        id=scene_id
    )
    worker.execution_manager.context = SceneSuperContext(
        node_scene,
    )

    return worker

