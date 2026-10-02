# TODO: refatorar essa classe para incluir alguns submanagers
import logging
from typing import Optional

from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.runtime.protocols.engine_events import EvtFailedProcess, IPCEngineEvent, JobStatus
from nodeserver.engine.runtime.job_graph_engine import JobStlGraphEngine
from nodeserver.engine.runtime.job_runtime_context import JobExecutionContext, SceneSuperContext, StepJobExecutionContext
from nodeserver.engine.workers.protocols.scene_worker_commands import IPCSceneWorkerCommand, StopWorkerCommand
from nodeserver.engine.workers.protocols.scene_worker_protocol import ISceneWorker, SceneWorkerCommandResponse, WorkerEngineEventWrapper
from nodeserver.engine.workers.protocols.scene_worker_states import SceneWorkerExecutionState
from nodeserver.engine.workers.protocols.scene_worker_states import SceneWorkerExecutionMode
from nodeserver.protocols.manifest.node.node_graph import SceneData

logger = logging.getLogger("nds.worker")

class SceneWorkerRunManager:
    _scene_worker: ISceneWorker

    engine: JobStlGraphEngine
    context: Optional[SceneSuperContext] = None
    _active_step_job: Optional[StepJobExecutionContext] = None

    execution_state: SceneWorkerExecutionState
    execution_mode: SceneWorkerExecutionMode

    target_fps: float = 60.0
    _target_execution_time: float = 1.0 / target_fps

    def __init__(
        self,
        scene_worker: ISceneWorker
    ) -> None:
        self._scene_worker = scene_worker
        self._build_engine()

        self._active_step_job = None
        self.execution_state = SceneWorkerExecutionState.STOPPED
        self.execution_mode = SceneWorkerExecutionMode.GRAPH_STEP


    def is_running(self) -> bool:
        return self.execution_state != SceneWorkerExecutionState.STOPPED

    def execute_graph(self) -> bool:
        if self.is_running():
            self._execute_scene_graph()
            return True
        
        return False
    

    def _build_engine(self):
        self.engine = JobStlGraphEngine()
    
    def _build_context(self, node_scene: NodeScene):
        if hasattr(self, "context"):
            logger.warning("SceneWorker context is being rebuilt")
        
        self.context = SceneSuperContext(
            node_scene,
            emit_event_callback=self._scene_worker.engine_event_receiver
        )

    def _load_scene_into_context(self, scene_data: SceneData):
        node_scene = self._scene_worker._create_new_scene(scene_data)
        self._build_context(node_scene)


    # Runtime Stuff:

    def _execute_scene_graph(self) -> Optional[WorkerEngineEventWrapper]:
        if not self.context:
            logger.error("Attempted to execute scene action without a loaded context")
            self.execution_state = SceneWorkerExecutionState.STOPPED
            return

        if self.execution_state == SceneWorkerExecutionState.STOPPED:
            return

        try:
            if self.execution_mode == SceneWorkerExecutionMode.FULL_GRAPH:
                job_context = JobExecutionContext(runtime=self.context)
                self.engine.execute_graph(job_context, reraise_exception=True)
            
            elif self.execution_mode == SceneWorkerExecutionMode.GRAPH_STEP:
                if self._active_step_job is None or self._active_step_job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.PARTIAL_SUCCESS):
                    self._active_step_job = StepJobExecutionContext(runtime=self.context)
                
                self.engine.execute_step(self._active_step_job, reraise_exception=True)
                if self._active_step_job.is_finished:
                    self._active_step_job = None

            if self.execution_state != SceneWorkerExecutionState.RUNNING_CONTINUOUS:
                self.execution_state = SceneWorkerExecutionState.STOPPED

        except Exception as e:
            logger.error("Failed to process scene graph")
            self.execution_state = SceneWorkerExecutionState.STOPPED
            
            self._active_step_job = None
            return WorkerEngineEventWrapper(
                engine_event=EvtFailedProcess(error=str(e))
            )
