from functools import singledispatchmethod

import logging
from multiprocessing import Queue
from pathlib import Path

from nodeserver.engine.utils.context_managers import scoped_sys_path
from nodeserver.engine.workers.base_scene_worker import BaseSceneWorker
from nodeserver.engine.workers.protocols.scene_worker_commands import AddNodeCommand, GraphStepCommand, LoadSceneCommand, ResetSceneCommand, UpdateExecutionModeCmd, UpdateExecutionStateCmd, IPCSceneWorkerCommand, LoadSceneDataCommand, PauseGraphCommand, UpdateTargetNodesCmd
from nodeserver.engine.workers.protocols.scene_worker_protocol import AddNodeCommandResponse, EvtFatalError, IPCSceneWorkerEvent, SceneWorkerCommandResponse
from nodeserver.engine.workers.protocols.scene_worker_states import SceneWorkerExecutionMode, SceneWorkerExecutionState
from nodeserver.protocols.manifest.node.node_graph import SceneData

logger = logging.getLogger("nds.worker")

# Scene Worker com implementação dos comandos
class SceneWorker(BaseSceneWorker):
    @singledispatchmethod
    def dispatch(self, cmd: IPCSceneWorkerCommand) -> SceneWorkerCommandResponse:
        return super().dispatch(cmd)

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

    @BaseSceneWorker.dispatch.register
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


def run_scene_worker_loop(
    scene_id: str, 
    plugins_folder: Path, 
    scenes_folder: Path, 
    command_queue: Queue[IPCSceneWorkerCommand], 
    event_queue: Queue[IPCSceneWorkerEvent]
):
    logger.info(f"Starting worker for scene {scene_id}")
    
    scene_worker = SceneWorker(scene_id, plugins_folder, scenes_folder, command_queue, event_queue)
    with scoped_sys_path(plugins_folder.parent):
        scene_worker.setup_plugins()
        scene_worker.runtime_loop()
