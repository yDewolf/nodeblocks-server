from functools import singledispatchmethod
import logging
from multiprocessing import Queue

from nodeserver.engine.workers.base_scene_worker import BaseSceneWorker
from nodeserver.engine.workers.protocols.scene_worker_commands import AddNodeCommand, GraphStepCommand, IPCSceneWorkerCommand, LoadSceneCommand, LoadSceneDataCommand, PauseGraphCommand, ResetSceneCommand, StopWorkerCommand, UpdateExecutionModeCmd, UpdateExecutionStateCmd, UpdateTargetNodesCmd
from nodeserver.engine.workers.protocols.scene_worker_protocol import AddNodeCommandResponse, IPCSceneWorkerEvent, SceneWorkerCommandResponse
from nodeserver.engine.workers.protocols.scene_worker_states import SceneWorkerExecutionMode, SceneWorkerExecutionState
from nodeserver.engine.workers.worker_command_handler import WorkerCommandHandler
from nodeserver.protocols.manifest.node.node_graph import SceneData

logger = logging.getLogger("nds.worker")

class SceneWorkerCommandHandler(WorkerCommandHandler[IPCSceneWorkerCommand, IPCSceneWorkerEvent, SceneWorkerCommandResponse]):
    command_queue: Queue[IPCSceneWorkerCommand]
    event_queue: Queue[IPCSceneWorkerEvent]
    scene_worker: BaseSceneWorker

    def __init__(
        self,
        scene_worker: BaseSceneWorker,
        command_queue: Queue[IPCSceneWorkerCommand],
        event_queue: Queue[IPCSceneWorkerEvent],
    ) -> None:
        self.scene_worker = scene_worker
        super().__init__(command_queue, event_queue)

    def create_failed_response(self, message: str, request_id: str) -> SceneWorkerCommandResponse:
        return SceneWorkerCommandResponse.failed(
            message=message,
            request_id=request_id
        )


    @property
    def scene_id(self): return self.scene_worker.scene_id

    @property
    def execution_manager(self): return self.scene_worker.execution_manager
    @property
    def scene_data_provider(self): return self.scene_worker.scene_data_provider
    @property
    def scene_state_provider(self): return self.scene_worker.scene_state_provider

    @singledispatchmethod
    def dispatch(self, cmd: IPCSceneWorkerCommand) -> SceneWorkerCommandResponse:
        logger.warning("Command %s was not implemented", cmd.__class__.__name__)
        return SceneWorkerCommandResponse.failed(
            message="Command was not implemented",
        )

    @dispatch.register
    def _(self, cmd: StopWorkerCommand):
        logger.info("Stopping scene worker...")
        self.scene_worker.active = False
        return SceneWorkerCommandResponse.successful()

    # Mode Updates:
    @dispatch.register
    def _(self, cmd: UpdateExecutionStateCmd):
        self.execution_manager.execution_state = cmd.state
        if not cmd.target_iterations is None: 
            self.execution_manager._target_iterations = cmd.target_iterations
            self.execution_manager._current_iteration = 0
        
        return SceneWorkerCommandResponse.successful()
    
    @dispatch.register
    def _(self, cmd: UpdateExecutionModeCmd):
        self.execution_manager.execution_mode = cmd.mode
        return SceneWorkerCommandResponse.successful()

    @dispatch.register
    def _(self, cmd: UpdateTargetNodesCmd):
        if not self.execution_manager.context:
            return SceneWorkerCommandResponse.failed(message="missing execution context")

        if cmd.target_nodes:
            all_nodes_exist = self.execution_manager.context.scene.graph.nodes_exist(cmd.target_nodes)
            if not all_nodes_exist:
                return SceneWorkerCommandResponse.failed(message="some nodes doesn't exist")
        
        self.execution_manager.target_nodes = cmd.target_nodes
        return SceneWorkerCommandResponse.successful()

    # Runtime Control:

    @dispatch.register
    def _(self, cmd: PauseGraphCommand):
        self.execution_manager.execution_state = SceneWorkerExecutionState.STOPPED
        return SceneWorkerCommandResponse.successful()

    @dispatch.register
    def _(self, cmd: GraphStepCommand):
        self.execution_manager.execution_state = SceneWorkerExecutionState.RUNNING
        self.execution_manager.execution_mode = SceneWorkerExecutionMode.GRAPH_STEP
        return SceneWorkerCommandResponse.successful()

    # Scene Actions:
    @dispatch.register
    def _(self, cmd: ResetSceneCommand):
        self.execution_manager.reset_state()
        return SceneWorkerCommandResponse.successful()

    @dispatch.register
    def _(self, cmd: LoadSceneCommand):
        scene_data = self.scene_data_provider.load_scene_data(cmd.scene_uid)
        if not scene_data:
            if not cmd.create_if_nonexistent:
                return SceneWorkerCommandResponse.failed(message="Couldn't find scene file")

            scene_data = SceneData(uid=self.scene_id, dependencies={})
            self.scene_data_provider.save_scene_data(scene_data)

        return self.dispatch(LoadSceneDataCommand(scene_data=scene_data, request_id=cmd.request_id))

    @dispatch.register
    def _(self, cmd: LoadSceneDataCommand):
        try:
            self.execution_manager._load_scene_into_context(cmd.scene_data)
        except Exception as e:
            return SceneWorkerCommandResponse.failed(message=str(e))
        
        return SceneWorkerCommandResponse.successful()

    @dispatch.register
    def _(self, cmd: AddNodeCommand) -> SceneWorkerCommandResponse:
        if not self.execution_manager.context:
            return AddNodeCommandResponse.failed("No active scene context loaded")

        try:
            node_instance = self.execution_manager.context.scene.create_node(
                node_fqn=cmd.nodetype_fqn,
                node_scene_data=cmd.node_data
            )
            return AddNodeCommandResponse.successful(node_uid=node_instance.uid)

        except Exception as e:
            return AddNodeCommandResponse.failed(message=str(e))