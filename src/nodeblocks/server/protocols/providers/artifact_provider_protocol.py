from abc import abstractmethod
from pathlib import Path
from typing import Any, Optional, Protocol


class IServerSceneArtifactProvider(Protocol):
    @abstractmethod
    def get_secure_artifact_path(self, scene_uid: str, node_uid: str, filename: str) -> Optional[Path]:
        pass
