from functools import singledispatchmethod

# nodeserver/engine/scene/scene_worker_runner.py
import logging
from multiprocessing import Queue
from pathlib import Path

from nodeserver.engine.utils.context_managers import scoped_sys_path
from nodeserver.engine.workers.base_scene_worker import BaseSceneWorker, WorkerExecutionState
from nodeserver.engine.workers.protocols.scene_worker_commands import AddNodeCommand, ExecuteGraphCommand, GraphExecutionModes, IPCSceneWorkerCommand, LoadSceneCommand, PauseGraphCommand
from nodeserver.engine.workers.protocols.scene_worker_protocol import AddNodeCommandResponse, EvtFatalError, IPCSceneWorkerEvent, SceneWorkerCommandResponse

logger = logging.getLogger("nds.worker")

# Scene Worker com implementação dos comandos
class SceneWorker(BaseSceneWorker):
    @singledispatchmethod
    def dispatch(self, cmd: IPCSceneWorkerCommand) -> SceneWorkerCommandResponse:
        return super().dispatch(cmd)

    # Runtime Control:
    @dispatch.register
    def _(self, cmd: ExecuteGraphCommand):
        if not self.context:
            return SceneWorkerCommandResponse.failed("SceneWorker context wasn't built")

        if cmd.mode == GraphExecutionModes.CONTINUOUS:
            self.execution_state = WorkerExecutionState.RUNNING_CONTINUOUS
        elif cmd.mode == GraphExecutionModes.FULL_GRAPH:
            self.execution_state = WorkerExecutionState.RUNNING_FULL_GRAPH
        elif cmd.mode == GraphExecutionModes.GRAPH_STEP:
            self.execution_state = WorkerExecutionState.RUNNING_SINGLE

        return SceneWorkerCommandResponse.successful()

    @dispatch.register
    def _(self, cmd: PauseGraphCommand):
        self.execution_state = WorkerExecutionState.STOPPED
        return SceneWorkerCommandResponse.successful(request_id=cmd.request_id)


    @dispatch.register
    def _(self, cmd: LoadSceneCommand):
        try:
            self._load_scene_into_context(cmd.scene_data)
        except Exception as e:
            return SceneWorkerCommandResponse.failed(message=str(e))
        
        return SceneWorkerCommandResponse.successful()

    @BaseSceneWorker.dispatch.register
    def _(self, cmd: AddNodeCommand) -> SceneWorkerCommandResponse:
        if not self.context:
            return SceneWorkerCommandResponse.failed("No active scene context loaded")

        try:
            node_instance = self.context.scene.create_node(
                node_fqn=cmd.nodetype_fqn,
                node_scene_data=cmd.node_data
            )
            return AddNodeCommandResponse.successful(node_uid=node_instance.uid)

        except Exception as e:
            return AddNodeCommandResponse.failed(message=str(e))


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
        scene_worker.runtime_loop()
