from functools import singledispatchmethod

# nodeserver/engine/scene/scene_worker_runner.py
import logging
from multiprocessing import Queue
from pathlib import Path

from nodeserver.engine.utils.context_managers import scoped_sys_path
from nodeserver.engine.workers.base_scene_worker import BaseSceneWorker
from nodeserver.engine.workers.protocols.scene_worker_commands import ExecuteGraphCommand, IPCSceneWorkerCommand, LoadSceneCommand
from nodeserver.engine.workers.protocols.scene_worker_protocol import EvtFatalError, IPCSceneWorkerEvent, SceneWorkerCommandResponse

logger = logging.getLogger("nds.worker")

# Scene Worker com implementação dos comandos
class SceneWorker(BaseSceneWorker):
    @BaseSceneWorker.dispatch.register
    def _(self, cmd: LoadSceneCommand):
        try:
            self._load_scene_into_context(cmd.scene_data)
        except Exception as e:
            return SceneWorkerCommandResponse.failed(message=str(e))
        
        return SceneWorkerCommandResponse.successful()

    @BaseSceneWorker.dispatch.register
    def _(self, cmd: ExecuteGraphCommand):
        if not self.context:
            return SceneWorkerCommandResponse.failed("SceneWorker context wasn't built")
        
        self.engine.execute_job(self.context)
        return SceneWorkerCommandResponse.successful()



def run_scene_worker_loop(
    scene_id: str, 
    plugins_folder: Path, 
    command_queue: Queue[IPCSceneWorkerCommand], 
    event_queue: Queue[IPCSceneWorkerEvent]
):
    logger.info(f"Starting worker for scene {scene_id}")

    scene_worker = SceneWorker(plugins_folder, command_queue, event_queue)
    with scoped_sys_path(plugins_folder.parent):
        scene_worker.setup_plugins()
        scene_worker.listen_to_commands()