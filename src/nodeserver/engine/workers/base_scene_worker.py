from enum import StrEnum
from functools import singledispatchmethod
import logging
from multiprocessing import Queue
from pathlib import Path
from queue import Empty
import time
from typing import Optional

from nodeserver.engine.helpers.plugin_subprocess_helper import PluginSubprocessHelper
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.plugins.plugin_node_provider import PluginNodeProvider
from nodeserver.engine.protocols.ipc_protocol import CmdStatus
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.protocols.node_provider import INodeProvider
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.engine.runtime.engine_events import EvtFailedProcess, IPCEngineEvent
from nodeserver.engine.runtime.graph_engine import StatelessGraphEngine
from nodeserver.engine.runtime.runtime_context import GraphRunContext
from nodeserver.engine.workers.protocols.scene_worker_commands import IPCSceneWorkerCommand, StopWorkerCommand
from nodeserver.engine.workers.protocols.scene_worker_protocol import EvtWorkerReady, IPCSceneWorkerEvent, SceneWorkerCommandResponse, WorkerEngineEventWrapper
from nodeserver.protocols.manifest.node.node_graph import SceneData

logger = logging.getLogger("nds.worker")

class WorkerExecutionState(StrEnum):
    STOPPED = "stopped"
    RUNNING_FULL_GRAPH = "running_full_graph"
    RUNNING_SINGLE = "running_single"
    RUNNING_CONTINUOUS = "continuous"

# Basico do basico do scene worker

# Server -> SceneWorker -> NodeScene
#           SceneWorker -> Engine
class BaseSceneWorker:
    registry: TypeRegistry
    plugin_manager: PluginManager
    node_provider: INodeProvider

    plugins_folder: Path

    command_queue: Queue[IPCSceneWorkerCommand]
    event_queue: Queue[IPCSceneWorkerEvent]

    engine: StatelessGraphEngine
    context: Optional[GraphRunContext] = None
    execution_state: WorkerExecutionState

    active: bool

    target_fps: float = 60.0
    _target_execution_time: float = 1.0 / target_fps

    def __init__(
        self, 
        plugins_folder: Path, 
        command_queue: Queue[IPCSceneWorkerCommand], 
        event_queue: Queue[IPCSceneWorkerEvent]
    ) -> None:
        self.command_queue = command_queue
        self.event_queue = event_queue

        self.plugins_folder = plugins_folder
        self.registry = TypeRegistry()
        self.plugin_manager = PluginManager(registry=self.registry)
        self.node_provider = PluginNodeProvider(self.plugin_manager)

        self._build_engine()
        self.active = True
        self.execution_state = WorkerExecutionState.STOPPED

    def setup_plugins(self):
        PluginSubprocessHelper.setup_and_load_plugins(
            self.plugins_folder, self.plugin_manager
        )
        self.event_queue.put(EvtWorkerReady())

    def runtime_loop(self):
        while self.active:
            self._process_pending_commands()
            if self.execution_state == WorkerExecutionState.RUNNING_CONTINUOUS:
                start_time = time.perf_counter()
                self._execute_scene_graph()

                elapsed = time.perf_counter() - start_time
                sleep_time = self._target_execution_time - elapsed
                if sleep_time > 0.002:
                    time.sleep(sleep_time)

            elif self.execution_state == WorkerExecutionState.RUNNING_SINGLE:
                self._execute_scene_graph()
                self.execution_state = WorkerExecutionState.STOPPED

            else:
                try:
                    command = self.command_queue.get(timeout=0.05)
                    self._handle_command(command)
                except Empty:
                    pass
    
    def engine_event_receiver(self, event: IPCEngineEvent):
        self.event_queue.put(WorkerEngineEventWrapper(
            engine_event=event
        ))


    def _build_engine(self):
        self.engine = StatelessGraphEngine()
    
    def _build_context(self, node_scene: NodeScene):
        if hasattr(self, "context"):
            logger.warning("SceneWorker context is being rebuilt")
        
        self.context = GraphRunContext(
            node_scene,
            emit_event_callback=self.engine_event_receiver
        )

    def _load_scene_into_context(self, scene_data: SceneData):
        # TODO: trocar package id por scene dependencies
        # TODO: verificar a versão do package no plugin manager
        if not self.plugin_manager.is_package_loaded(scene_data.package_id):
            raise Exception("Scene Package is not loaded") # TODO: maybe use plugin exceptions here 

        node_scene = NodeScene(self.registry, self.node_provider)
        node_scene.load_from_scene_data(scene_data)
        self._build_context(node_scene)


    # Runtime Stuff:

    def _process_pending_commands(self):
        while not self.command_queue.empty():
            try:
                command = self.command_queue.get_nowait()
                self._handle_command(command)
            except Empty:
                break

    def _handle_command(self, command: IPCSceneWorkerCommand):
        try:
            cmd_response = self.dispatch(command)
            if not cmd_response:
                logger.warning("Command '%s' missing response", command.__class__.__name__)
                cmd_response = SceneWorkerCommandResponse.failed(
                    message="No response returned by handler",
                    request_id=command.request_id
                )
            else:
                if hasattr(cmd_response, "request_id") and cmd_response.request_id is None:
                    object.__setattr__(cmd_response, "request_id", command.request_id)

                logger.debug("%s -> %s", command.__class__.__name__, cmd_response.status)
        
        except Exception as e:
            logger.error("Error executing command %s", command.__class__.__name__)
            cmd_response = SceneWorkerCommandResponse.failed(
                message=f"Internal error: {str(e)}",
                request_id=command.request_id
            )
            return

        self.event_queue.put(cmd_response)


    def _execute_scene_graph(self):
        if not self.context:
            logger.error("Attempted to execute scene action without a loaded context")
            self.execution_state = WorkerExecutionState.STOPPED
            return

        try:
            match self.execution_state:
                # TODO:
                # case WorkerExecutionState.RUNNING_SINGLE:
                #     self.engine.execute_job_step(self.context, reraise_exception=True)
                case _:
                    self.engine.execute_job(self.context, reraise_exception=True)

        except Exception as e:
            logger.error("Failed to process scene graph")
            self.execution_state = WorkerExecutionState.STOPPED

            self.event_queue.put(WorkerEngineEventWrapper(
                engine_event=EvtFailedProcess(error=str(e))
            ))

    # Commands

    @singledispatchmethod
    def dispatch(self, cmd: IPCSceneWorkerCommand) -> SceneWorkerCommandResponse:
        logger.warning("Command %s was not implemented", cmd.__class__.__name__)
        return SceneWorkerCommandResponse.failed(
            message="Command was not implemented",
        )

    @dispatch.register
    def _stop_worker_cmd(self, cmd: StopWorkerCommand):
        logger.info("Stopping scene worker...")
        self.active = False
        return SceneWorkerCommandResponse.successful()

