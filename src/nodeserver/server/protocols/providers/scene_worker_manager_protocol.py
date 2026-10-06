from abc import abstractmethod
from typing import Protocol

from nodeserver.engine.workers.scene.protocols.scene_worker_commands import IPCSceneWorkerCommand

class ISceneWorkerManager(Protocol):
    @abstractmethod
    def send_command_to_scene(self, scene_id: str, command: IPCSceneWorkerCommand) -> None:
        pass
