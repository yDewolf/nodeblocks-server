from abc import abstractmethod
from pathlib import Path
from typing import Any, Protocol


class ISceneArtifactProvider(Protocol):
    _scene_uid: str
    @property
    def scene_uid(self): return self._scene_uid
    
    def __init__(self, scene_uid: str) -> None:
        self._scene_uid = scene_uid

    @abstractmethod
    def load_artifact(self, artifact_path: Path) -> Any:
        pass

    @abstractmethod
    def get_node_artifact_path(self, node_uid: str, filename: str, hash: str, extension: str) -> Path:
        """Returns a file path that includes a hash"""
        pass

    @abstractmethod
    def get_formatted_filename(self, filename: str, hash: str, extension: str) -> str:
        pass
