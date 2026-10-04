import logging
from multiprocessing import Queue
from pathlib import Path

from nodeserver.engine.utils.context_managers import scoped_sys_path
from nodeserver.engine.workers.base_scene_worker import BaseSceneWorker
from nodeserver.engine.workers.protocols.scene_worker_commands import IPCSceneWorkerCommand
from nodeserver.engine.workers.protocols.scene_worker_protocol import IPCSceneWorkerEvent
from nodeserver.engine.workers.scene_worker_cmd_handler import SceneWorkerCommandHandler

logger = logging.getLogger("nds.worker")

def run_scene_worker_loop(
    scene_id: str, 
    plugins_folder: Path, 
    scenes_folder: Path, 
    command_queue: Queue[IPCSceneWorkerCommand], 
    event_queue: Queue[IPCSceneWorkerEvent]
):
    logger.info(f"Starting worker for scene {scene_id}")

    scene_worker = BaseSceneWorker(scene_id, plugins_folder, scenes_folder)
    command_handler = SceneWorkerCommandHandler(scene_worker, command_queue, event_queue)
    scene_worker.set_command_handler(command_handler)
    
    with scoped_sys_path(plugins_folder.parent):
        scene_worker.setup_plugins()
        scene_worker.runtime_loop()
