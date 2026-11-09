from nodeserver.engine.protocols.node.scene_states import LogicNodeState
from pathlib import Path

from nodeserver.engine.protocols.providers.scene_artifact_provider import ISceneArtifactProvider
from nodeserver.engine.protocols.providers.scene_provider import ISceneDataProvider
from nodeserver.engine.protocols.providers.scene_state_provider import ISceneStateProvider
from nodeserver.protocols.manifest.node.node_graph import SceneData


class NoSceneDataProvider(ISceneDataProvider):
    def validate_scene_data(self, scene_data: SceneData) -> None:
        return

    def load_scene_data(self, scene_uid: str) -> SceneData | None:
        return

    def save_scene_data(self, scene_data: SceneData):
        raise NotImplementedError()


class NoSceneStateProvider(ISceneStateProvider):
    def _setup_folder(self):
        return

    def _save_node_state(self, node_uid: str, node_state: LogicNodeState):
        return

    def _load_node_state(self, node_uid: str) -> LogicNodeState | None:
        return

    def get_node_state_folder(self, node_uid: str) -> Path:
        raise NotImplementedError()


class NoSceneArtifactProvider(ISceneArtifactProvider):
    def cleanup_artifacts(self):
        raise NotImplementedError()

    def commit_node_artifact(self, node_uid: str, new_path: Path | list[Path]):
        raise NotImplementedError()

    def make_node_artifact_path(self, node_uid: str, filename: str, hash: str, extension: str) -> Path:
        raise NotImplementedError()

    def get_formatted_filename(self, filename: str, hash: str, extension: str) -> str:
        raise NotImplementedError()
