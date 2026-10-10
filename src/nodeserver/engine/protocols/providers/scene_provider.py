
from abc import abstractmethod
from typing import Optional, Protocol

from nodeserver.protocols.manifest.node.node_graph import SceneData


class ISceneDataProvider(Protocol):
    @abstractmethod
    def validate_scene_data(self, scene_data: SceneData) -> None:
        pass

    @abstractmethod
    def load_scene_data(self, scene_uid: str) -> Optional[SceneData]:
        pass

    @abstractmethod
    def save_scene_data(self, scene_data: SceneData):
        pass

