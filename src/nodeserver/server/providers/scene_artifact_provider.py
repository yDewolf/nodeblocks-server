from pathlib import Path

from nodeserver.server.protocols.providers.artifact_provider_protocol import IServerSceneArtifactProvider


class ServerFileArtifactProvider(IServerSceneArtifactProvider):
    scenes_root: Path

    def __init__(self, scenes_root: Path) -> None:
        self.scenes_root = scenes_root

    def get_secure_artifact_path(self, scene_uid: str, node_uid: str, filename: str) -> Path | None:
        target_path = self.get_node_artifacts_folder(scene_uid, node_uid) / filename

        if not str(target_path).startswith(str(self.get_artifacts_folder(scene_uid))):
            return None

        return target_path

    # -- utils

    def get_node_artifacts_folder(self, scene_uid: str, node_uid: str) -> Path:
        return self.get_artifacts_folder(scene_uid) / node_uid
    
    def get_artifacts_folder(self, scene_uid: str) -> Path:
        return self.scenes_root / scene_uid / "artifacts"

