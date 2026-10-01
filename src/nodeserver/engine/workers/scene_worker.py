# nodeserver/engine/scene/scene_worker_runner.py
import logging
from multiprocessing import Queue
from pathlib import Path
from typing import Any, Optional

from nodeserver.engine.helpers.plugin_subprocess_helper import PluginSubprocessHelper
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.engine.runtime.engine_events import IPCEngineEvent
from nodeserver.engine.runtime.graph_engine import StatelessGraphEngine
from nodeserver.engine.runtime.runtime_context import GraphRunContext
from nodeserver.engine.utils.context_managers import scoped_sys_path
from nodeserver.engine.workers.protocols.scene_worker_commands import IPCSceneWorkerCommand, StopWorkerCommand
from nodeserver.engine.workers.protocols.scene_worker_protocol import EvtFatalError, EvtWorkerReady, WorkerEngineEventWrapper, IPCSceneWorkerEvent

logger = logging.getLogger("nds.worker")

# Server -> SceneWorker -> NodeScene
#           SceneWorker -> Engine
class SceneWorker:
    registry: TypeRegistry
    plugin_manager: PluginManager

    plugins_folder: Path

    command_queue: Queue[IPCSceneWorkerCommand]
    event_queue: Queue[IPCSceneWorkerEvent]

    engine: StatelessGraphEngine
    context: GraphRunContext

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

    def setup_plugins(self):
        PluginSubprocessHelper.setup_and_load_plugins(
            self.plugins_folder, self.plugin_manager
        )
        self.event_queue.put(EvtWorkerReady())

    
    def listen_to_commands(self):
        while True:
            command: IPCSceneWorkerCommand = self.command_queue.get()
            if isinstance(command, StopWorkerCommand):
                logger.info("Stopping scene worker...")
                break

            self._execute_command(command)


    def engine_event_receiver(self, event: IPCEngineEvent):
        self.event_queue.put(WorkerEngineEventWrapper(
            engine_event=event
        ))


    def _execute_command(self, msg: IPCSceneWorkerCommand) -> Optional[IPCSceneWorkerEvent]:
        match msg:
                

            case _:
                logger.warning(f"No implementation for command: {type(msg)}")

    
    def _build_context(self, node_scene: NodeScene):
        self.context = GraphRunContext(node_scene, )


def run_scene_worker_loop(
    scene_id: str, 
    plugins_folder: Path, 
    command_queue: Queue[IPCSceneWorkerCommand], 
    event_queue: Queue[IPCSceneWorkerEvent]
):
    logging.basicConfig(level=logging.INFO)
    logger.info(f"Starting worker for scene {scene_id}")

    scene_worker = SceneWorker(plugins_folder, command_queue, event_queue)
    with scoped_sys_path(plugins_folder.parent):
        try:
            scene_worker.setup_plugins()
            scene_worker.listen_to_commands()

        except Exception as e:
            logger.exception("Critical failure in scene worker loop.")
            event_queue.put(EvtFatalError(error=str(e)))
