
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


class NoSceneDataProvider(ISceneDataProvider):
    def validate_scene_data(self, scene_data: SceneData) -> None:
        raise NotImplementedError()

    def load_scene_data(self, scene_uid: str) -> SceneData | None:
        raise NotImplementedError()

    def save_scene_data(self, scene_data: SceneData):
        raise NotImplementedError()
