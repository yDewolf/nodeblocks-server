from nodeserver.engine.protocols.node.scene_states import LogicNodeState
from pathlib import Path

from nodeserver.engine.protocols.providers.scene_provider import ISceneDataProvider
from nodeserver.engine.protocols.providers.scene_state_provider import ISceneStateProvider
from nodeserver.protocols.manifest.node.node_graph import SceneData


class NoSceneDataProvider(ISceneDataProvider):
    def validate_scene_data(self, scene_data: SceneData) -> None:
        raise NotImplementedError()

    def load_scene_data(self, scene_uid: str) -> SceneData | None:
        raise NotImplementedError()

    def save_scene_data(self, scene_data: SceneData):
        raise NotImplementedError()


class NoSceneStateProvider(ISceneStateProvider):
    def _setup_folder(self):
        raise NotImplementedError()

    def _save_node_state(self, node_uid: str, node_state: LogicNodeState):
        raise NotImplementedError()

    def _load_node_state(self, node_uid: str) -> LogicNodeState | None:
        raise NotImplementedError()

    def get_node_state_folder(self, node_uid: str) -> Path:
        raise NotImplementedError()
