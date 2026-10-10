import asyncio
import logging
from multiprocessing import Queue
from pathlib import Path

from nodeserver.engine.plugins.plugin_compiler import PluginCompiler
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.providers.file_scene_provider import FileSceneDataProvider, FileSceneStateProvider
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.engine.utils.context_managers import scoped_sys_path
from nodeserver.engine.workers.scene.scene_worker import SceneWorker
from nodeserver.engine.workers.scene.protocols.scene_worker_commands import IPCSceneWorkerCommand
from nodeserver.engine.workers.scene.protocols.scene_worker_protocol import IPCSceneWorkerEvent
from nodeserver.engine.workers.scene.scene_worker_cmd_handler import SceneWorkerCommandHandler

logger = logging.getLogger("nds.worker")

def run_scene_worker_loop(
    scene_id: str, 
    plugins_folder: Path, 
    scenes_folder: Path, 
    command_queue: Queue[IPCSceneWorkerCommand], 
    event_queue: Queue[IPCSceneWorkerEvent]
):
    logger.info(f"Starting worker for scene {scene_id}")

    plugin_manager = PluginManager.new(plugins_base_package=plugins_folder.name)
    file_data_provider = FileSceneDataProvider(scene_id, plugin_manager, scenes_folder)
    state_provider = FileSceneStateProvider(scene_id)
    state_provider.scenes_root = file_data_provider.scenes_root

    scene_worker = SceneWorker(
        scene_id, plugins_folder, 
        file_data_provider, state_provider,
        plugin_manager=plugin_manager
    )
    command_handler = SceneWorkerCommandHandler(scene_worker, command_queue, event_queue)
    scene_worker.set_command_handler(command_handler)

    with scoped_sys_path(plugins_folder.parent):
        scene_worker.setup_plugins()
        scene_worker.runtime_loop()
        # asyncio.run(scene_worker.run())
