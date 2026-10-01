from functools import singledispatchmethod

# nodeserver/engine/scene/scene_worker_runner.py
import logging
from multiprocessing import Queue
from pathlib import Path

from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.utils.context_managers import scoped_sys_path
from nodeserver.engine.workers.base_scene_worker import BaseSceneWorker
from nodeserver.engine.workers.protocols.scene_worker_commands import ExecuteGraphCommand, IPCSceneWorkerCommand, LoadSceneCommand
from nodeserver.engine.workers.protocols.scene_worker_protocol import EvtFatalError, IPCSceneWorkerEvent, SceneWorkerCommandResponse

logger = logging.getLogger("nds.worker")

# Scene Worker com implementação dos comandos
class SceneWorker(BaseSceneWorker):
    @BaseSceneWorker.dispatch.register
    def _(self, cmd: LoadSceneCommand):
        node_scene = NodeScene(self.registry, self.node_provider)
            
        self._build_context(node_scene)

    @BaseSceneWorker.dispatch.register
    def _(self, cmd: ExecuteGraphCommand):
        pass



def run_scene_worker_loop(
    scene_id: str, 
    plugins_folder: Path, 
    command_queue: Queue[IPCSceneWorkerCommand], 
    event_queue: Queue[IPCSceneWorkerEvent]
):
    logger.info(f"Starting worker for scene {scene_id}")

    scene_worker = SceneWorker(plugins_folder, command_queue, event_queue)
    with scoped_sys_path(plugins_folder.parent):
        try:
            scene_worker.setup_plugins()
            scene_worker.listen_to_commands()

        except Exception as e:
            logger.exception("Critical failure in scene worker loop.")
            event_queue.put(EvtFatalError(error=str(e)))
