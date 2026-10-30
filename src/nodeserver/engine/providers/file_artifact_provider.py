import logging
from pathlib import Path

from nodeserver.engine.protocols.providers.scene_artifact_provider import ISceneArtifactProvider
from nodeserver.engine.providers.file_scene_provider import FileSceneDataProvider

logger = logging.getLogger("nds.engine")

KEEP_ARTIFACT_BATCH_PER_NODE = 3
class FileArtifactProvider(ISceneArtifactProvider):
    data_provider: FileSceneDataProvider
    recent_artifacts: dict[str, list[list[Path]]]

    def __init__(self, file_scene_data_provider: FileSceneDataProvider) -> None:
        super().__init__(file_scene_data_provider.scene_uid)
        self.data_provider = file_scene_data_provider
        self.recent_artifacts = {}
        self._setup_folder()
    

    def _setup_folder(self): 
        self.get_artifacts_folder().mkdir(exist_ok=True)

    def cleanup_artifacts(self):
        folder = self.get_artifacts_folder()
        if not folder.exists():
            return

        logger.warning("Cleaning artifacts folder %s", folder)
        active_paths = set()
        for node_uid, batches in self.recent_artifacts.items():
            if not batches:
                continue
            
            latest_batch = batches[-1]
            for path in latest_batch:
                active_paths.add(path.resolve())
            
            self.recent_artifacts[node_uid] = [latest_batch]

        for node_dir in folder.iterdir():
            if not node_dir.is_dir():
                continue
            
            for file_path in node_dir.rglob("*"):
                if not file_path.is_file(): continue
                if file_path.resolve() not in active_paths:
                    try:
                        file_path.unlink()
                    except Exception as e:
                        logger.warning("Failed to remove obsolete artifact %s: %s", file_path, e)


    def commit_node_artifact(self, node_uid: str, new_path: Path | list[Path]):
        new_path_batch = new_path if isinstance(new_path, list) else [new_path]
        recent = self.recent_artifacts.get(node_uid, [])

        if len(recent) >= KEEP_ARTIFACT_BATCH_PER_NODE:
            self.cleanup_node_artifacts(node_uid)

        if not node_uid in self.recent_artifacts:
            self.recent_artifacts[node_uid] = [new_path_batch]
            return
        
        self.recent_artifacts[node_uid].append(new_path_batch)


    def make_node_artifact_path(self, node_uid: str, filename: str, hash: str, extension: str) -> Path:
        return self.get_node_artifacts_folder(node_uid) / self.get_formatted_filename(filename, hash, extension)

    def get_formatted_filename(self, filename: str, hash: str, extension: str) -> str:
        return f"{hash}.{filename}.{extension}"

    # -- utils

    def cleanup_node_artifacts(self, node_uid: str):
        artifacts = self.recent_artifacts.get(node_uid, [])
        if len(artifacts) == 0:
            return

        least_recent_batch = self.recent_artifacts[node_uid].pop(0)
        for path in least_recent_batch:
            if not path.exists(): continue
            try:
                path.unlink()
            
            except Exception:
                logger.warning("Failed to remove old path for node %s. Old path: %s", node_uid, path)


    def get_node_artifacts_folder(self, node_uid: str) -> Path:
        return self.get_artifacts_folder() / node_uid

    def get_artifacts_folder(self) -> Path:
        scene_folder = self.data_provider.get_scene_folder(self.data_provider.scene_uid)
        return scene_folder / "artifacts"
