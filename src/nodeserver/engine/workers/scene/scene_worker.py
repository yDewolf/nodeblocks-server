import asyncio
import logging
from pathlib import Path
from typing import Optional

from nodeserver.engine.helpers.node_scene_helper import NodeSceneHelper
from nodeserver.engine.helpers.plugin_subprocess_helper import PluginSubprocessHelper
from nodeserver.engine.plugins.plugin_manager import PluginManager
from nodeserver.engine.plugins.plugin_node_provider import PluginNodeProvider
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.protocols.providers.node_provider import INodeProvider
from nodeserver.engine.protocols.providers.scene_provider import ISceneDataProvider
from nodeserver.engine.protocols.providers.scene_state_provider import ISceneStateProvider
from nodeserver.engine.runtime.protocols.engine_events import IPCEngineEvent
from nodeserver.engine.utils.benchmark_managers import BenchmarkTimer, FramePacer
from nodeserver.engine.workers.scene.protocols.scene_worker_commands import IPCSceneWorkerCommand, SaveSceneCommand
from nodeserver.engine.workers.scene.protocols.scene_worker_protocol import EvtWorkerReady, ISceneWorker, SceneWorkerCommandResponse, WorkerEngineEventWrapper
from nodeserver.engine.workers.worker_command_handler import WorkerCommandHandler
from nodeserver.engine.workers.scene.worker_execution_manager import SceneWorkerRunManager
from nodeserver.protocols.manifest.node.node_graph import SceneData

logger = logging.getLogger("nds.worker")

SCENE_AUTOSAVE_INTERVAL: float = 3.0 # seconds

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

    def runtime_loop(self):
        with BenchmarkTimer(
            "SceneWorkerRuntime", log_every=500
        ) as bench:
            while self.active:
                if self.command_handler:
                    self.command_handler.process_pending_commands()
                
                if self.execution_manager.is_running():
                    # FIXME: dar uma olhada no quanto de overhead isso aqui cria
                    with FramePacer(target_fps=self.target_fps, min_sleep=0.008):
                        self.execution_manager.execute_graph()
                
                elif self.command_handler:
                    self.command_handler.process_command(timeout=0.05)
                
                bench.step()

    def engine_event_receiver(self, event: IPCEngineEvent):
        if self.command_handler:
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

    # FIXME: for some reason this isn't working
    # Tasks
    # async def cleanup(self):
    #     logger.info("Finishing Scene Worker (%s)...", self.scene_id)
    #     for task in self.tasks:
    #         task.cancel()
    #         try:
    #             await task
    #         except asyncio.CancelledError:
    #             pass
                
    #         logger.info("Finished scene worker task: %s", task.get_name())

    # async def setup_tasks(self):
    #     self.tasks = []
    #     task = asyncio.create_task(self.autosave_task(), name="scene_autosave")
    #     self.tasks.append(task)

    # async def run(self):
    #     await self.setup_tasks()
    #     try:
    #         self.runtime_loop()
    #     finally:
    #         await self.cleanup()

    # async def autosave_task(self):
    #     while True:
    #         try:
    #             logger.info("hi")
    #             if not self.execution_manager.context or not self.autosave:
    #                 await asyncio.sleep(10.0)
    #                 continue
                
    #             logger.info("Autosaving scene %s", self.scene_id)
    #             if self.command_handler:
    #                 self.command_handler._handle_command(SaveSceneCommand())
    #             else:
    #                 self.execution_manager.context.scene.save_state()
    #             await asyncio.sleep(SCENE_AUTOSAVE_INTERVAL)
    #         except asyncio.CancelledError:
    #             break
