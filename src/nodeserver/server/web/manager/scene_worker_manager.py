import asyncio
from pathlib import Path
import time
from typing import Any, Callable, Coroutine, Optional

from nodeserver.engine.workers.scene.protocols.scene_worker_commands import CheckExecutionState, IPCSceneWorkerCommand, LoadSceneCommand
from nodeserver.engine.workers.scene.protocols.scene_worker_protocol import IPCSceneWorkerEvent, CheckExecutionStateResponse
from nodeserver.engine.workers.scene.protocols.scene_worker_states import SceneWorkerExecutionState
from nodeserver.server.workers.scene_worker_controller import SceneWorkerController


EventCallback = Callable[[str, IPCSceneWorkerEvent], Coroutine[Any, Any, None]]
CHECK_STATUS_INTERVAL = 10.0 # seconds
class SceneWorkerManager:
    plugins_folder: Path
    scenes_folder: Path

    _tasks: list[asyncio.Task]
    _on_event_callback: Optional[EventCallback] = None
    
    # scene id -> worker controller
    active_workers: dict[str, SceneWorkerController]
    # scene id -> state, timestamp (when it changed to this state)
    worker_statuses: dict[str, tuple[SceneWorkerExecutionState, float]]
    
    def __init__(self, plugins_folder: Path, scenes_folder: Path) -> None:
        self.plugins_folder = plugins_folder
        self.scenes_folder = scenes_folder

        self.active_workers = {}
        self.worker_statuses = {}
        self._tasks = []

    def get_or_create_worker(self, scene_id: str, auto_load: bool = True) -> SceneWorkerController:
        if scene_id not in self.active_workers:
            controller = SceneWorkerController(scene_id, self.plugins_folder, self.scenes_folder)
            controller.start()
            self.active_workers[scene_id] = controller

            controller.send_command(CheckExecutionState())
            if auto_load:
                controller.send_command(LoadSceneCommand(scene_uid=scene_id, create_if_nonexistent=True))
        
        return self.active_workers[scene_id]
    
    def send_command_to_scene(self, scene_id: str, command: IPCSceneWorkerCommand) -> bool:
        worker = self.active_workers.get(scene_id)
        if not worker:
            return False
        
        worker.send_command(command)
        return True        

    def set_event_callback(self, callback: EventCallback):
        self._on_event_callback = callback

    # Async

    async def start(self):
        self._tasks.append(
            asyncio.create_task(self._poll_worker_events())
        )
        self._tasks.append(
            asyncio.create_task(self._poll_worker_status())
        )

    async def stop(self):
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        for worker in self.active_workers.values():
            worker.stop()

        self.active_workers.clear()

    async def _poll_worker_status(self):
        while True:
            try:
                for scene_id, worker in list(self.active_workers.items()):
                    worker.send_command(CheckExecutionState())
                
                await asyncio.sleep(CHECK_STATUS_INTERVAL)
            except asyncio.CancelledError:
                break

    async def _poll_worker_events(self):
        loop = asyncio.get_running_loop()
        while True:
            try:
                for scene_id, worker in list(self.active_workers.items()):
                    while not worker._event_queue.empty():
                        event = await loop.run_in_executor(None, worker._event_queue.get_nowait)
                        
                        await self.repass_event(scene_id, event)

                await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(0.1)

    async def repass_event(self, scene_id: str, event: IPCSceneWorkerEvent):
        if isinstance(event, CheckExecutionStateResponse):
            if scene_id in self.worker_statuses:
                if self.worker_statuses[scene_id][0] == event.state:
                    return
            
            self.worker_statuses[scene_id] = (
                event.state,
                time.time()
            )

        if self._on_event_callback:
            await self._on_event_callback(scene_id, event)

    def kill_scene_worker(self, scene_id: str):
        if not scene_id in self.active_workers:
            return
        
        worker_controller = self.active_workers.pop(scene_id)
        worker_controller.stop()
        del self.worker_statuses[scene_id]
    
    
    def get_scene_id_by_state(self, state: SceneWorkerExecutionState, min_elapsed_time: float = 0) -> list[tuple[str, float]]:
        workers: list[tuple[str, float]] = []
        now = time.time()
        for scene_id, (worker_state, timestamp) in self.worker_statuses.items():
            if worker_state == state and (timestamp + min_elapsed_time) <= now:
                workers.append((scene_id, timestamp))

        return workers
