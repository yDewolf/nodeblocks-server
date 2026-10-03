from functools import singledispatchmethod
import logging
from multiprocessing import Queue
from pathlib import Path
from queue import Empty
import time

from nodeserver.engine.helpers.node_scene_helper import NodeSceneHelper
from nodeserver.engine.helpers.plugin_subprocess_helper import PluginSubprocessHelper
from nodeserver.engine.helpers.scene_file_reader import SceneFileReader
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.plugins.plugin_node_provider import PluginNodeProvider
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.protocols.node_provider import INodeProvider
from nodeserver.engine.protocols.scene_provider import ISceneDataProvider
from nodeserver.engine.protocols.scene_state_provider import ISceneStateProvider
from nodeserver.engine.providers.file_scene_provider import FileSceneDataProvider, FileSceneStateProvider
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.engine.runtime.protocols.engine_events import IPCEngineEvent
from nodeserver.engine.utils.benchmark_managers import BenchmarkTimer, FramePacer
from nodeserver.engine.workers.protocols.scene_worker_commands import IPCSceneWorkerCommand, StopWorkerCommand
from nodeserver.engine.workers.protocols.scene_worker_protocol import EvtWorkerReady, IPCSceneWorkerEvent, ISceneWorker, SceneWorkerCommandResponse, WorkerEngineEventWrapper
from nodeserver.engine.workers.worker_execution_manager import SceneWorkerRunManager
from nodeserver.protocols.manifest.node.node_graph import SceneData

logger = logging.getLogger("nds.worker")
benchmark_logger = logging.getLogger("nds.benchmark")

# Basico do basico do scene worker

# Server -> SceneWorker -> NodeScene
#           SceneWorker -> Engine
class BaseSceneWorker(ISceneWorker):
    scene_id: str

    plugin_manager: PluginManager
    node_provider: INodeProvider
    scene_data_provider: ISceneDataProvider
    scene_state_provider: ISceneStateProvider

    execution_manager: SceneWorkerRunManager

    plugins_folder: Path

    command_queue: Queue[IPCSceneWorkerCommand]
    event_queue: Queue[IPCSceneWorkerEvent]

    active: bool

    target_fps: float = 60.0

    def __init__(
        self,
        scene_id: str,
        plugins_folder: Path,
        scenes_folder: Path,
        command_queue: Queue[IPCSceneWorkerCommand], 
        event_queue: Queue[IPCSceneWorkerEvent]
    ) -> None:
        self.scene_id = scene_id
        self.command_queue = command_queue
        self.event_queue = event_queue

        self.plugins_folder = plugins_folder
        self.plugin_manager = PluginManager(registry=TypeRegistry())
        self.node_provider = PluginNodeProvider(self.plugin_manager)
        
        self.scene_state_provider = FileSceneStateProvider(self.scene_id)
        self.scene_data_provider = FileSceneDataProvider(self.scene_id, self.plugin_manager, scenes_folder) 
        
        self.execution_manager = SceneWorkerRunManager(self)
        self.active = True


    def setup_plugins(self):
        PluginSubprocessHelper.setup_and_load_plugins(
            self.plugins_folder, self.plugin_manager
        )
        self.event_queue.put(EvtWorkerReady())

    def runtime_loop(self):
        with BenchmarkTimer(
            "SceneWorkerRuntime", log_every=500
        ) as bench:
            
            while self.active:
                self._process_pending_commands()
                if self.execution_manager.is_running():
                    # FIXME: dar uma olhada no quanto de overhead isso aqui cria
                    with FramePacer(target_fps=self.target_fps, min_sleep=0.008):
                        self.execution_manager.execute_graph()
                
                else:
                    try:
                        command = self.command_queue.get(timeout=0.05)
                        self._handle_command(command)
                    except Empty:
                        pass
                
                bench.step()

    # ISceneWorker
    
    def engine_event_receiver(self, event: IPCEngineEvent):
        self.event_queue.put(WorkerEngineEventWrapper(
            engine_event=event
        ))

    def _create_new_scene(self, scene_data: SceneData) -> NodeScene:
        return NodeSceneHelper.create_new_scene(
            self.plugin_manager, 
            self.node_provider, self.scene_data_provider, self.scene_state_provider, 
            scene_data, 
            scene_id=self.scene_id
        )

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

