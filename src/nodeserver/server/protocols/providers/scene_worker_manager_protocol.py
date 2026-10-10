from abc import abstractmethod
from typing import Protocol

from nodeserver.engine.workers.scene.protocols.scene_worker_commands import IPCSceneWorkerCommand
from nodeserver.engine.workers.scene.protocols.scene_worker_states import SceneWorkerExecutionState

class ISceneWorkerManager(Protocol):
    @abstractmethod
    def send_command_to_scene(self, scene_id: str, command: IPCSceneWorkerCommand) -> None:
        pass

    @abstractmethod
    def get_scene_state(self, scene_id: str) -> SceneWorkerExecutionState:
        pass
