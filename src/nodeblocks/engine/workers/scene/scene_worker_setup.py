import asyncio
import logging
from multiprocessing.queues import Queue
from pathlib import Path

from nodeblocks.engine.engine_env import ENGINE_ENV
from nodeblocks.engine.helpers.plugin_subprocess_helper import PluginSubprocessHelper, get_plugin_sys_paths
from nodeblocks.engine.plugins.plugin_manager import PluginManager
from nodeblocks.engine.providers.file_artifact_provider import FileArtifactProvider
from nodeblocks.engine.providers.file_scene_provider import FileSceneDataProvider, FileSceneStateProvider
from nodeblocks.engine.utils.context_managers import scoped_sys_path
from nodeblocks.engine.workers.scene.scene_worker import SceneWorker
from nodeblocks.engine.workers.scene.protocols.scene_worker_commands import IPCSceneWorkerCommand
from nodeblocks.engine.workers.scene.protocols.scene_worker_protocol import IPCSceneWorkerEvent
from nodeblocks.engine.workers.scene.scene_worker_cmd_handler import SceneWorkerCommandHandler

logger = logging.getLogger("nds.worker")

def run_scene_worker_loop(
    scene_id: str, 
    plugins_folder: Path,
    extraction_folder: Path, 
    scenes_folder: Path, 
    command_queue: Queue[IPCSceneWorkerCommand], 
    event_queue: Queue[IPCSceneWorkerEvent],
    scene_autosave_interval: float
):
    logger.info(f"Starting worker for scene {scene_id}")

    plugin_manager = PluginManager.new(plugins_base_package=plugins_folder.name)
    file_data_provider = FileSceneDataProvider(scene_id, plugin_manager, scenes_folder)
    state_provider = FileSceneStateProvider(scene_id)
    state_provider.scenes_root = file_data_provider.scenes_root

    artifact_provider = FileArtifactProvider(file_data_provider)

    scene_worker = SceneWorker(
        scene_id, plugins_folder, extraction_folder,
        file_data_provider, state_provider,
        plugin_manager=plugin_manager,
        scene_artifact_provider=artifact_provider
    )
    scene_worker.scene_autosave_interval = scene_autosave_interval
    
    command_handler = SceneWorkerCommandHandler(scene_worker, command_queue, event_queue)
    scene_worker.set_command_handler(command_handler)

    libs_dir = PluginSubprocessHelper.get_libs_dir(plugins_folder)
    paths = get_plugin_sys_paths(plugins_folder, extraction_folder, libs_dir)
    with scoped_sys_path(paths):
        scene_worker.setup_plugins()
        # scene_worker.runtime_loop()
        asyncio.run(scene_worker.run())

    artifact_provider.cleanup_artifacts()
