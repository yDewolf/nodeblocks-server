import pytest

from nodeserver.engine.workers.base_scene_worker import BaseSceneWorker
from nodeserver.engine.workers.protocols.scene_worker_commands import AddNodeCommand, GraphStepCommand, LoadSceneDataCommand, PauseGraphCommand, StopWorkerCommand, UpdateExecutionModeCmd, UpdateExecutionStateCmd, UpdateTargetNodesCmd
from nodeserver.engine.workers.protocols.scene_worker_protocol import AddNodeCommandResponse, SceneWorkerCommandResponse
from nodeserver.engine.workers.protocols.scene_worker_states import SceneWorkerExecutionMode, SceneWorkerExecutionState
from nodeserver.protocols.manifest.node.node_graph import SceneData

@pytest.fixture
def scene_data() -> SceneData:
    return SceneData(
        dependencies={
            "test_package": "0.0.0"
        },
        nodes={},
        connections={}
    )

class TestSceneWorkerCommandResponses:
    def test_update_execution_state_cmd(self, worker: BaseSceneWorker):
        cmd = UpdateExecutionStateCmd(
            state=SceneWorkerExecutionState.RUNNING_CONTINUOUS,
            target_iterations=10
        )

        response = worker.dispatch(cmd)

        assert isinstance(response, SceneWorkerCommandResponse)
        assert response.is_success
        assert worker.execution_manager.execution_state == SceneWorkerExecutionState.RUNNING_CONTINUOUS
        assert worker.execution_manager._target_iterations == 10
        assert worker.execution_manager._current_iteration == 0

    def test_update_execution_mode_cmd(self, worker: BaseSceneWorker):
        cmd = UpdateExecutionModeCmd(mode=SceneWorkerExecutionMode.GRAPH_STEP)

        response = worker.dispatch(cmd)

        assert isinstance(response, SceneWorkerCommandResponse)
        assert response.is_success
        assert worker.execution_manager.execution_mode == SceneWorkerExecutionMode.GRAPH_STEP

    def test_update_target_nodes_without_context(self, worker: BaseSceneWorker):
        cmd = UpdateTargetNodesCmd(target_nodes=["node_1"])

        response = worker.dispatch(cmd)

        assert isinstance(response, SceneWorkerCommandResponse)
        assert not response.is_success

    def test_update_target_nodes_non_existent_node(self, worker: BaseSceneWorker, scene_data: SceneData):
        worker.execution_manager._load_scene_into_context(scene_data)

        cmd = UpdateTargetNodesCmd(target_nodes=["non_existent_node_id"])
        response = worker.dispatch(cmd)

        assert isinstance(response, SceneWorkerCommandResponse)
        assert not response.is_success

    def test_update_target_nodes_empty_list_success(self, worker: BaseSceneWorker, scene_data: SceneData):
        worker.execution_manager._load_scene_into_context(scene_data)

        cmd = UpdateTargetNodesCmd(target_nodes=[])
        response = worker.dispatch(cmd)

        assert isinstance(response, SceneWorkerCommandResponse)
        assert response.is_success
        assert worker.execution_manager.target_nodes == []

    def test_pause_graph_command(self, worker: BaseSceneWorker):
        worker.execution_manager.execution_state = SceneWorkerExecutionState.RUNNING
        cmd = PauseGraphCommand()

        response = worker.dispatch(cmd)

        assert isinstance(response, SceneWorkerCommandResponse)
        assert response.is_success
        assert worker.execution_manager.execution_state == SceneWorkerExecutionState.STOPPED

    def test_graph_step_command(self, worker: BaseSceneWorker):
        cmd = GraphStepCommand()

        response = worker.dispatch(cmd)

        assert isinstance(response, SceneWorkerCommandResponse)
        assert response.is_success
        assert worker.execution_manager.execution_state == SceneWorkerExecutionState.RUNNING
        assert worker.execution_manager.execution_mode == SceneWorkerExecutionMode.GRAPH_STEP

    def test_load_scene_command(self, worker: BaseSceneWorker, scene_data: SceneData):
        cmd = LoadSceneDataCommand(scene_data=scene_data)

        response = worker.dispatch(cmd)

        assert isinstance(response, SceneWorkerCommandResponse)
        assert response.is_success
        assert worker.execution_manager.context is not None
        assert worker.execution_manager.context.scene is not None

    def test_add_node_command_without_context(self, worker: BaseSceneWorker):
        cmd = AddNodeCommand(nodetype_fqn="math.Add", node_data=None)

        response = worker.dispatch(cmd)

        assert isinstance(response, AddNodeCommandResponse)
        assert not response.is_success

    def test_add_node_command_unregistered_type(self, worker: BaseSceneWorker, scene_data: SceneData):
        worker.execution_manager._load_scene_into_context(scene_data)
        cmd = AddNodeCommand(nodetype_fqn="unknown_package:NonExistentNode", node_data=None)

        response = worker.dispatch(cmd)

        assert isinstance(response, AddNodeCommandResponse)
        assert not response.is_success

    def test_stop_worker_command(self, worker: BaseSceneWorker):
        cmd = StopWorkerCommand()

        response = worker.dispatch(cmd)

        assert isinstance(response, SceneWorkerCommandResponse)
        assert response.is_success
        assert worker.active is False
