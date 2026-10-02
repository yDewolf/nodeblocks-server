from queue import Empty
import threading
import time

from nodeserver.engine.runtime.protocols.engine_context import NodeExecutionStatus
from nodeserver.engine.runtime.protocols.engine_events import EvtNodeStatusChanged
from nodeserver.engine.workers.protocols.scene_worker_commands import GraphStepCommand, LoadSceneCommand, PauseGraphCommand, StopWorkerCommand, UpdateExecutionModeCmd, UpdateExecutionStateCmd
from nodeserver.engine.workers.protocols.scene_worker_protocol import IPCSceneWorkerEvent, WorkerEngineEventWrapper
from nodeserver.engine.workers.protocols.scene_worker_states import SceneWorkerExecutionMode, SceneWorkerExecutionState
from nodeserver.engine.workers.scene_worker import SceneWorker
from nodeserver.protocols.manifest.node.node_graph import SceneData


class TestSceneWorkerExecutionMatrix:

    def test_running_and_graph_step_executes_single_node_and_pauses(
        self, worker: SceneWorker, populated_scene: SceneData
    ):
        worker.command_queue.put(LoadSceneCommand(scene_data=populated_scene))
        worker.command_queue.put(UpdateExecutionModeCmd(mode=SceneWorkerExecutionMode.GRAPH_STEP))
        worker.command_queue.put(UpdateExecutionStateCmd(state=SceneWorkerExecutionState.RUNNING))

        thread = threading.Thread(target=worker.runtime_loop, daemon=True)
        thread.start()
        time.sleep(0.4)

        worker.command_queue.put(StopWorkerCommand())
        thread.join()

        ctx = worker.execution_manager._active_step_job
        assert ctx is not None
        assert worker.execution_manager.execution_state == SceneWorkerExecutionState.STOPPED

        assert ctx.node_status.get("node_0") == NodeExecutionStatus.SUCCESS
        assert ctx.node_status.get("node_1") == NodeExecutionStatus.PENDING

    def test_running_and_full_graph_executes_all_nodes_and_pauses(
        self, worker: SceneWorker, populated_scene: SceneData
    ):
        worker.command_queue.put(LoadSceneCommand(scene_data=populated_scene))
        worker.command_queue.put(UpdateExecutionModeCmd(mode=SceneWorkerExecutionMode.FULL_GRAPH))
        worker.command_queue.put(UpdateExecutionStateCmd(state=SceneWorkerExecutionState.RUNNING))

        thread = threading.Thread(target=worker.runtime_loop, daemon=True)
        thread.start()

        time.sleep(0.4)
        worker.command_queue.put(StopWorkerCommand())
        thread.join()

        ctx = worker.execution_manager._last_finished_job
        assert ctx is not None

        assert worker.execution_manager.execution_state == SceneWorkerExecutionState.STOPPED
        assert ctx.node_status.get("node_0") == NodeExecutionStatus.SUCCESS
        assert ctx.node_status.get("node_1") == NodeExecutionStatus.SUCCESS

    def test_running_continuous_and_graph_step_steps_continuously(
        self, worker: SceneWorker, populated_scene: SceneData
    ):
        worker.command_queue.put(LoadSceneCommand(scene_data=populated_scene))
        worker.command_queue.put(UpdateExecutionModeCmd(mode=SceneWorkerExecutionMode.GRAPH_STEP))
        worker.command_queue.put(UpdateExecutionStateCmd(state=SceneWorkerExecutionState.RUNNING_CONTINUOUS))

        thread = threading.Thread(target=worker.runtime_loop, daemon=True)
        thread.start()

        time.sleep(0.4)
        worker.command_queue.put(PauseGraphCommand())
        worker.command_queue.put(StopWorkerCommand())
        thread.join(timeout=2.0)
        assert worker.execution_manager.execution_state == SceneWorkerExecutionState.STOPPED

        events: list[IPCSceneWorkerEvent] = []
        try:
            while True:
                events.append(worker.event_queue.get(timeout=0.03))
        except Empty:
            pass

        node_status_events: int = 0
        for event in events:
            if isinstance(event, WorkerEngineEventWrapper):
                if isinstance(event.engine_event, EvtNodeStatusChanged):
                    node_status_events += 1
        
        ctx = worker.execution_manager._last_finished_job
        assert ctx is not None
        assert node_status_events > 1
        assert worker.execution_manager.execution_state == SceneWorkerExecutionState.STOPPED

    def test_running_continuous_and_full_graph_executes_full_graph_repeatedly(
        self, worker: SceneWorker, populated_scene: SceneData
    ):
        worker.command_queue.put(LoadSceneCommand(scene_data=populated_scene))
        worker.command_queue.put(UpdateExecutionModeCmd(mode=SceneWorkerExecutionMode.FULL_GRAPH))
        worker.command_queue.put(UpdateExecutionStateCmd(state=SceneWorkerExecutionState.RUNNING_CONTINUOUS))

        thread = threading.Thread(target=worker.runtime_loop, daemon=True)
        thread.start()

        time.sleep(0.4)
        worker.command_queue.put(PauseGraphCommand())
        worker.command_queue.put(StopWorkerCommand())
        thread.join(timeout=2.0)
        assert worker.execution_manager.execution_state == SceneWorkerExecutionState.STOPPED

        events: list[IPCSceneWorkerEvent] = []
        try:
            while True:
                events.append(worker.event_queue.get(timeout=0.03))
        except Empty:
            pass

        ctx = worker.execution_manager._last_finished_job
        assert ctx is not None

        assert ctx.node_status.get("node_0") == NodeExecutionStatus.SUCCESS
        assert ctx.node_status.get("node_1") == NodeExecutionStatus.SUCCESS
        assert worker.execution_manager.execution_state == SceneWorkerExecutionState.STOPPED

    def test_graph_step_command_shortcut_behavior(
        self, worker: SceneWorker, populated_scene: SceneData
    ):
        worker.command_queue.put(LoadSceneCommand(scene_data=populated_scene))
        
        worker.command_queue.put(GraphStepCommand())
        thread = threading.Thread(target=worker.runtime_loop, daemon=True)
        thread.start()
        time.sleep(0.4)

        worker.command_queue.put(StopWorkerCommand())
        thread.join(timeout=2.0)

        ctx = worker.execution_manager._active_step_job
        assert ctx is not None

        assert worker.execution_manager.execution_state == SceneWorkerExecutionState.STOPPED
        assert ctx.node_status.get("node_0") == NodeExecutionStatus.SUCCESS
        assert ctx.node_status.get("node_1") == NodeExecutionStatus.PENDING
