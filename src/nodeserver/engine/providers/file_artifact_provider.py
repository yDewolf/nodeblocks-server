from pathlib import Path

from nodeserver.engine.protocols.providers.scene_artifact_provider import ISceneArtifactProvider
from nodeserver.engine.providers.file_scene_provider import FileSceneDataProvider


class FileArtifactProvider(ISceneArtifactProvider):
    data_provider: FileSceneDataProvider

    def __init__(self, file_scene_data_provider: FileSceneDataProvider) -> None:
        super().__init__(file_scene_data_provider.scene_uid)
        self.data_provider = file_scene_data_provider
        self._setup_folder()
    

    def _setup_folder(self): 
        self.get_artifacts_folder().mkdir(exist_ok=True)


    def get_node_artifact_path(self, node_uid: str, filename: str, hash: str, extension: str) -> Path:
        return self.get_node_artifacts_folder(node_uid) / f"{filename}_{hash}.{extension}"

    # -- utils

    def get_node_artifacts_folder(self, node_uid: str) -> Path:
        return self.get_artifacts_folder() / node_uid

    def get_artifacts_folder(self) -> Path:
        scene_folder = self.data_provider.get_scene_folder(self.data_provider.scene_uid)
        return scene_folder / "artifacts"
