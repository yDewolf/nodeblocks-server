from abc import abstractmethod
from pathlib import Path
from typing import Protocol, Union


class ISceneArtifactProvider(Protocol):
    _scene_uid: str
    @property
    def scene_uid(self): return self._scene_uid
    
    def __init__(self, scene_uid: str) -> None:
        self._scene_uid = scene_uid

    @abstractmethod
    def cleanup_artifacts(self):
        pass

    @abstractmethod
    def commit_node_artifact(self, node_uid: str, new_path: Union[Path, list[Path]]):
        # TODO: avaliar se isso deve ficar no RuntimeContext ou aqui mesmo
        pass

    @abstractmethod
    def make_node_artifact_path(self, node_uid: str, filename: str, hash: str, extension: str) -> Path:
        """Returns a file path that includes a hash"""
        pass

    @abstractmethod
    def get_formatted_filename(self, filename: str, hash: str, extension: str) -> str:
        pass
