import asyncio
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

from nodeserver.engine.workers.protocols.scene_worker_commands import IPCSceneWorkerCommand, LoadSceneCommand
from nodeserver.engine.workers.protocols.scene_worker_protocol import IPCSceneWorkerEvent
from nodeserver.server.workers.scene_worker_controller import SceneWorkerController


EventCallback = Callable[[str, IPCSceneWorkerEvent], Coroutine[Any, Any, None]]
class SceneWorkerManager:
    plugins_folder: Path
    scenes_folder: Path

    _event_dispatcher_task: Optional[asyncio.Task]
    _on_event_callback: Optional[EventCallback] = None
    
    # scene id -> worker controller
    active_workers: dict[str, SceneWorkerController]
    
    def __init__(self, plugins_folder: Path, scenes_folder: Path) -> None:
        self.plugins_folder = plugins_folder
        self.scenes_folder = scenes_folder

        self.active_workers = {}
        self._event_dispatcher_task = None

    def get_or_create_worker(self, scene_id: str, auto_load: bool = True) -> SceneWorkerController:
        if scene_id not in self.active_workers:
            controller = SceneWorkerController(scene_id, self.plugins_folder, self.scenes_folder)
            controller.start()
            self.active_workers[scene_id] = controller

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
        if self._event_dispatcher_task is None:
            self._event_dispatcher_task = asyncio.create_task(self._poll_worker_events())

    async def stop(self):
        if self._event_dispatcher_task:
            self._event_dispatcher_task.cancel()
            try:
                await self._event_dispatcher_task
            except asyncio.CancelledError:
                pass

        for worker in self.active_workers.values():
            worker.stop()

        self.active_workers.clear()

    async def _poll_worker_events(self):
        loop = asyncio.get_running_loop()

        while True:
            try:
                for scene_id, worker in list(self.active_workers.items()):
                    while not worker._event_queue.empty():
                        event = await loop.run_in_executor(None, worker._event_queue.get_nowait)
                        
                        if self._on_event_callback:
                            await self._on_event_callback(scene_id, event)

                await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(0.1)
