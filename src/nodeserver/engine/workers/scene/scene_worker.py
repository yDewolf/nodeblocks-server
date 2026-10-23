import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

from nodeserver.engine.helpers.node_scene_helper import NodeSceneHelper
from nodeserver.engine.helpers.plugin_subprocess_helper import PluginSubprocessHelper
from nodeserver.engine.plugins.api.plugin_datatype import PluginDatatype
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.plugins.plugin_node_provider import PluginNodeProvider
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.protocols.providers.node_provider import INodeProvider
from nodeserver.engine.protocols.providers.scene_provider import ISceneDataProvider
from nodeserver.engine.protocols.providers.scene_state_provider import ISceneStateProvider
from nodeserver.engine.runtime.protocols.engine_events import NodeExecutionStatus
from nodeserver.engine.runtime.protocols.engine_events import EvtNodeStatusChanged, IPCEngineEvent
from nodeserver.engine.runtime.protocols.engine_tracker import EngineTracker
from nodeserver.engine.utils.benchmark_managers import BenchmarkTimer, FramePacer
from nodeserver.engine.workers.protocols.general_worker_protocol import EvtWorkerReady, EvtWorkerStopped
from nodeserver.engine.workers.scene.protocols.scene_worker_commands import IPCSceneWorkerCommand, SaveSceneCommand
from nodeserver.engine.workers.scene.protocols.scene_worker_protocol import ISceneWorker, SceneWorkerCommandResponse, UpdateExecutionConfigResponse, WorkerEngineEventWrapper
from nodeserver.engine.workers.scene.protocols.scene_worker_states import SceneWorkerExecutionMode, SceneWorkerExecutionState
from nodeserver.engine.workers.worker_command_handler import WorkerCommandHandler
from nodeserver.engine.workers.scene.worker_execution_manager import SceneWorkerRunManager
from nodeserver.protocols.manifest.node.node_graph import SceneData

logger = logging.getLogger("nds.worker")

SCENE_AUTOSAVE_INTERVAL: float = 2 * 60 # seconds

# Basico do basico do scene worker

# Server -> SceneWorker -> NodeScene
#           SceneWorker -> Engine
class SceneWorker(ISceneWorker):
    scene_id: str

    command_handler: Optional[WorkerCommandHandler] = None

    plugin_manager: PluginManager
    node_provider: INodeProvider
    scene_data_provider: ISceneDataProvider
    scene_state_provider: ISceneStateProvider

    execution_manager: SceneWorkerRunManager

    plugins_folder: Path

    active: bool
    target_fps: float = 60.0

    autosave: bool = True
    tasks: list[asyncio.Task]

    def __init__(
        self,
        scene_id: str,
        plugins_folder: Path,
        scene_data_provider: ISceneDataProvider,
        scene_state_provider: ISceneStateProvider,
        plugin_manager: Optional[PluginManager] = None,
    ) -> None:
        self.scene_id = scene_id

        self.plugins_folder = plugins_folder
        self.plugin_manager = plugin_manager or PluginManager.new()
        self.node_provider = PluginNodeProvider(self.plugin_manager)
        
        self.scene_state_provider = scene_state_provider
        self.scene_data_provider = scene_data_provider 
        
        self.execution_manager = SceneWorkerRunManager(self)
        self.active = True

    def set_command_handler(self, handler: WorkerCommandHandler):
        self.command_handler = handler

    def setup_plugins(self):
        logger.info("Setting up %s's scene worker plugins...", self.scene_id)
        PluginSubprocessHelper.setup_and_load_plugins(
            self.plugins_folder, self.plugin_manager
        )
        if self.command_handler:
            self.command_handler.event_queue.put(EvtWorkerReady())

    async def runtime_loop(self):
        with BenchmarkTimer(
            "SceneWorkerRuntime", log_every=500
        ) as bench:
            while self.active:
                if self.command_handler:
                    self.command_handler.process_pending_commands()
                
                if self.execution_manager.is_running():
                    # FIXME: dar uma olhada no quanto de overhead isso aqui cria
                    initial_state, initial_mode = self.execution_manager.execution_mode.value, self.execution_manager.execution_mode.value
                    with FramePacer(target_fps=self.target_fps, min_sleep=0.008):
                        self.execution_manager.execute_graph()

                    if initial_state != self.execution_manager.execution_state.value or initial_mode != self.execution_manager.execution_mode.value:
                        self.on_runtime_updated(self.execution_manager.execution_state, self.execution_manager.execution_mode)
                
                elif self.command_handler:
                    self.command_handler.process_command(timeout=0.05)
                
                bench.step()
                await asyncio.sleep(0.001)

        if self.execution_manager.context:
            self.execution_manager.context.scene.save_state()
        
        if self.command_handler:
            self.command_handler.event_queue.put(EvtWorkerStopped())

    def on_runtime_updated(self, state: SceneWorkerExecutionState, mode: SceneWorkerExecutionMode):
        if self.command_handler:
            self.command_handler.event_queue.put(
                # FIXME: this should be a sync message instead of a command response
                UpdateExecutionConfigResponse.successful(
                    request_id="sync_worker_state", state=state, mode=mode, 
                    target_iterations=self.execution_manager._target_iterations, 
                    target_nodes=self.execution_manager.target_nodes
                )
            )

    def engine_event_receiver(self, event: IPCEngineEvent):
        if not self.command_handler:
            return

        if isinstance(event, EvtNodeStatusChanged) and self.execution_manager.context:
            if event.status == NodeExecutionStatus.SUCCESS and event.node_result:
                instance = self.execution_manager.context.scene.graph.ensure_node(event.node_uid)

                serialized_result: dict[str, Any] = {}
                for slot_id, value in event.node_result.items():
                    if isinstance(value, PluginDatatype):
                        serialized_result[slot_id] = value.serialize()
                        continue
                    
                    datatype_fqn = instance.slots[slot_id].datatype_fqn
                    datatype = self.plugin_manager.registry.get_datatype_python_type(datatype_fqn)
                    if datatype and issubclass(datatype, PluginDatatype):
                        serialized_result[slot_id] = datatype.serialize_value(value)
                        continue

                    logger.error("Failed to find a datatype for slot output (type: %s)", datatype_fqn)
                    serialized_result[slot_id] = value

                event = EvtNodeStatusChanged(
                    job_id=event.job_id,
                    node_uid=event.node_uid,
                    status=event.status,
                    node_result=serialized_result,
                    tracker=EngineTracker.node(event.node_uid)
                )
                
        self.command_handler.event_queue.put(WorkerEngineEventWrapper(
            engine_event=event
        ))

    def dispatch(self, cmd: IPCSceneWorkerCommand) -> Optional[SceneWorkerCommandResponse]:
        if self.command_handler:
            return self.command_handler.dispatch(cmd)
        
        return None

    def _create_new_scene(self, scene_data: SceneData) -> NodeScene:
        return NodeSceneHelper.create_new_scene(
            self.plugin_manager, 
            self.node_provider, self.scene_data_provider, self.scene_state_provider, 
            scene_data, 
            scene_id=self.scene_id
        )

    # Tasks
    async def cleanup(self):
        logger.info("Finishing Scene Worker (%s)...", self.scene_id)
        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
                
            logger.info("Finished scene worker task: %s", task.get_name())

    async def setup_tasks(self):
        self.tasks = []
        task = asyncio.create_task(self.autosave_task(), name="scene_autosave")
        self.tasks.append(task)

    async def run(self):
        await self.setup_tasks()
        try:
            await self.runtime_loop()
        finally:
            await self.cleanup()

    async def autosave_task(self):
        while True:
            try:
                if not self.execution_manager.context or not self.autosave:
                    await asyncio.sleep(10.0)
                    continue
                
                logger.info("Autosaving scene %s", self.scene_id)
                if self.command_handler:
                    self.command_handler._handle_command(SaveSceneCommand())
                else:
                    self.execution_manager.context.scene.save_state()
                await asyncio.sleep(SCENE_AUTOSAVE_INTERVAL)
            except asyncio.CancelledError:
                break
