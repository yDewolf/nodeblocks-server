from functools import singledispatchmethod
import logging
from multiprocessing import Queue
from pathlib import Path
from typing import Optional

from nodeserver.engine.helpers.plugin_subprocess_helper import PluginSubprocessHelper
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.plugins.plugin_node_provider import PluginNodeProvider
from nodeserver.engine.protocols.ipc_protocol import CmdStatus
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.protocols.node_provider import INodeProvider
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.engine.runtime.engine_events import IPCEngineEvent
from nodeserver.engine.runtime.graph_engine import StatelessGraphEngine
from nodeserver.engine.runtime.runtime_context import GraphRunContext
from nodeserver.engine.workers.protocols.scene_worker_commands import IPCSceneWorkerCommand, StopWorkerCommand
from nodeserver.engine.workers.protocols.scene_worker_protocol import EvtWorkerReady, IPCSceneWorkerEvent, SceneWorkerCommandResponse, WorkerEngineEventWrapper


logger = logging.getLogger("nds.worker")

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

    active: bool

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

        self.active = True

    def setup_plugins(self):
        PluginSubprocessHelper.setup_and_load_plugins(
            self.plugins_folder, self.plugin_manager
        )
        self.event_queue.put(EvtWorkerReady())

    
    def listen_to_commands(self):
        while self.active:
            command: IPCSceneWorkerCommand = self.command_queue.get()
            self.dispatch(command)


    def engine_event_receiver(self, event: IPCEngineEvent):
        self.event_queue.put(WorkerEngineEventWrapper(
            engine_event=event
        ))

    
    def _build_context(self, node_scene: NodeScene):
        self.context = GraphRunContext(node_scene, )


    @singledispatchmethod
    def dispatch(self, cmd: IPCSceneWorkerCommand) -> SceneWorkerCommandResponse:
        logger.warning("Command %s was not implemented", cmd.__class__.__name__)
        return SceneWorkerCommandResponse(
            status=CmdStatus.failed(message="Command was not implemented"),
        )

    @dispatch.register
    def _stop_worker_cmd(self, cmd: StopWorkerCommand):
        logger.info("Stopping scene worker...")
        self.active = False
        return SceneWorkerCommandResponse(
            status=CmdStatus.successful()
        )

