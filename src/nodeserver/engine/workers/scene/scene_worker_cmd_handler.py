from functools import singledispatchmethod
import logging
from multiprocessing import Queue

from nodeserver.engine.workers.scene.scene_worker import SceneWorker
from nodeserver.engine.workers.scene.protocols.scene_worker_commands import AddConnectionsCommand, AddNodesCommand, CheckExecutionState, GetSceneDataCommand, GraphStepCommand, IPCSceneWorkerCommand, LoadSceneCommand, LoadSceneDataCommand, PauseGraphCommand, RemoveConnectionsCommand, RemoveNodesCommand, ResetSceneCommand, SaveSceneCommand, SetSceneAutosaveCommand, StopWorkerCommand, UpdateExecutionModeCmd, UpdateExecutionStateCmd, UpdateNodesCommand, UpdateTargetNodesCmd
from nodeserver.engine.workers.scene.protocols.scene_worker_protocol import AddConnCommandResponse, AddNodeCommandResponse, GetSceneDataResponse, IPCSceneWorkerEvent, SceneWorkerCommandResponse, CheckExecutionStateResponse
from nodeserver.engine.workers.scene.protocols.scene_worker_states import SceneWorkerExecutionMode, SceneWorkerExecutionState
from nodeserver.engine.workers.worker_command_handler import WorkerCommandHandler
from nodeserver.protocols.manifest.node.node_graph import SceneData

logger = logging.getLogger("nds.worker")

class SceneWorkerCommandHandler(WorkerCommandHandler[IPCSceneWorkerCommand, IPCSceneWorkerEvent, SceneWorkerCommandResponse]):
    command_queue: Queue[IPCSceneWorkerCommand]
    event_queue: Queue[IPCSceneWorkerEvent]
    scene_worker: SceneWorker

    def __init__(
        self,
        scene_worker: SceneWorker,
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

    # Commands:

    @dispatch.register
    def _(self, cmd: StopWorkerCommand):
        logger.info("Stopping scene worker...")
        self.scene_worker.active = False
        return SceneWorkerCommandResponse.successful()


    @dispatch.register
    def _(self, cmd: CheckExecutionState) -> CheckExecutionStateResponse:
        return CheckExecutionStateResponse.successful(
            state=self.execution_manager.execution_state,
            mode=self.execution_manager.execution_mode
        )

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
    def _(self, cmd: GetSceneDataCommand):
        if not self.execution_manager.context:
            return GetSceneDataResponse.failed(message="No active scene context loaded") 

        try:
            scene_data = self.execution_manager.context.scene.as_scene_data()
        except Exception as e:
            return GetSceneDataResponse.failed(message=str(e))
    
        return GetSceneDataResponse.successful(scene_data=scene_data)
        
    
    @dispatch.register
    def _(self, cmd: SaveSceneCommand):
        if not self.execution_manager.context:
            return SceneWorkerCommandResponse.failed(message="No active scene context loaded") 
        try:
            self.execution_manager.context.scene.save_state()
        except Exception as e:
            return SceneWorkerCommandResponse.failed(message=str(e))

        return SceneWorkerCommandResponse.successful()

    @dispatch.register
    def _(self, cmd: SetSceneAutosaveCommand):
        self.scene_worker.autosave = cmd.autosave
        return SceneWorkerCommandResponse.successful()

    # Node Commands:

    @dispatch.register
    def _(self, cmd: AddNodesCommand) -> AddNodeCommandResponse:
        if not self.execution_manager.context:
            return AddNodeCommandResponse.failed("No active scene context loaded")

        try:
            added_nodes: list[str] = []
            for cmd_data in cmd.nodes:
                # FIXME: this might cause problems
                if cmd_data.node_data and cmd_data.uid:
                    cmd_data.node_data.uid = cmd_data.uid
                
                node_instance = self.execution_manager.context.scene.create_node(
                    node_fqn=cmd_data.nodetype_fqn,
                    node_scene_data=cmd_data.node_data
                )
                added_nodes.append(node_instance.uid)
            
            return AddNodeCommandResponse.successful(added_nodes)

        except Exception as e:
            return AddNodeCommandResponse.failed(message=str(e))

    @dispatch.register
    def _(self, cmd: RemoveNodesCommand) -> SceneWorkerCommandResponse:
        if not self.execution_manager.context:
            return AddNodeCommandResponse.failed("No active scene context loaded")

        # TODO: return each node status
        for uid in cmd.uids:
            successful = self.execution_manager.context.scene.delete_node(uid)
            if not successful:
                return SceneWorkerCommandResponse.failed(f"Failed to remove node: {uid}")

        return SceneWorkerCommandResponse.successful()

    @dispatch.register
    def _(self, cmd: UpdateNodesCommand) -> SceneWorkerCommandResponse:
        if not self.execution_manager.context:
            return SceneWorkerCommandResponse.failed("No active scene context loaded")
        
        # TODO: Return each node status
        for uid, cmd_data in cmd.nodes.items():
            node = self.execution_manager.context.scene.get_logic_node(uid)
            if not node:
                return SceneWorkerCommandResponse.failed("This node doesn't exist in the current scene")

            node.update_parameters(cmd_data.data)
            if cmd_data.position:
                node.scene_data.position = cmd_data.position
        
        return SceneWorkerCommandResponse.successful()

    # Connection Commands:

    @dispatch.register
    def _(self, cmd: AddConnectionsCommand) -> AddConnCommandResponse:
        if not self.execution_manager.context:
            return AddConnCommandResponse.failed("No active scene context loaded")

        try:
            added_conns: list[str] = []
            for conn in cmd.connections:
                conn_data = self.execution_manager.context.scene.graph.connect(
                    conn_uid=conn.uid,
                    from_node_id=conn.from_node_id, from_slot_id=conn.from_slot_id,
                    to_node_id=conn.to_node_id, to_slot_id=conn.to_slot_id
                )
                if conn_data:
                    added_conns.append(conn_data.uid)
            
            if added_conns == []:            
                return AddConnCommandResponse.failed("Couldn't connect the slots")
            
            return AddConnCommandResponse.successful(added_conns)

        except Exception as e:
            # TODO: better exception handling here
            return AddConnCommandResponse.failed(message=str(e))

    
    @dispatch.register
    def _(self, cmd: RemoveConnectionsCommand) -> SceneWorkerCommandResponse:
        if not self.execution_manager.context:
            return SceneWorkerCommandResponse.failed("No active scene context loaded")

        # TODO: return each conn status
        for conn_uid in cmd.uids:
            successful = self.execution_manager.context.scene.graph.disconnect(conn_uid)
            if not successful:
                return SceneWorkerCommandResponse.failed(f"Failed to remove connection: {conn_uid}")

        return SceneWorkerCommandResponse.successful()
