import multiprocessing as mp
from multiprocessing.context import SpawnContext, SpawnProcess
from queue import Empty
from pathlib import Path
from typing import Any, Optional

from nodeserver.engine.workers.protocols.scene_worker_commands import IPCSceneWorkerCommand, StopWorkerCommand
from nodeserver.engine.workers.protocols.scene_worker_protocol import EvtWorkerReady, IPCSceneWorkerEvent
from nodeserver.engine.workers.scene_worker import run_scene_worker_loop

class SceneWorkerController:
    scene_id: str
    plugins_folder: Path

    _ctx: SpawnContext

    _command_queue: mp.Queue[IPCSceneWorkerCommand]
    _event_queue: mp.Queue[IPCSceneWorkerEvent]
    _process: Optional[SpawnProcess]

    def __init__(self, scene_id: str, plugins_folder: Path):
        self.scene_id = scene_id
        self.plugins_folder = plugins_folder
        
        self._ctx = mp.get_context("spawn")
        
        self._command_queue = self._ctx.Queue()
        self._event_queue = self._ctx.Queue()
        self._process = None


    def start(self, wait_ready: bool = False):
        if self._process and self._process.is_alive():
            return

        self._process = self._ctx.Process(
            target=run_scene_worker_loop,
            args=(self.scene_id, self.plugins_folder, self._command_queue, self._event_queue),
            daemon=True
        )
        self._process.start()
        if wait_ready:
            is_ready = False
            
            while not is_ready:
                events = self.get_events()
                for event in events:
                    if isinstance(event, EvtWorkerReady):
                        is_ready = True
                        break


    def stop(self, timeout: float = 3.0):
        if not self._process or not self._process.is_alive():
            return

        self.send_command(StopWorkerCommand())
        self._process.join(timeout)
        
        if self._process.is_alive():
            self._process.terminate()
            self._process.join()


    def send_command(self, command: IPCSceneWorkerCommand):
        self._command_queue.put(command)


    def get_events(self) -> list[IPCSceneWorkerEvent]:
        events: list[IPCSceneWorkerEvent] = []
        try:
            while True:
                events.append(self._event_queue.get_nowait())
        
        except Empty:
            pass
            
        return events
