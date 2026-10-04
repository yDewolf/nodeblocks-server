import logging
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from nodeserver.engine.helpers.scene_file_reader import SceneFileReader
from nodeserver.engine.plugins.plugin_spec_manager import PluginSpecManager
from nodeserver.engine.protocols.node.scene_states import LogicNodeState
from nodeserver.engine.protocols.providers.scene_provider import ISceneDataProvider
from nodeserver.engine.protocols.providers.scene_state_provider import ISceneStateProvider
from nodeserver.protocols.manifest.node.node_graph import SceneData

logger = logging.getLogger("nds.engine")

# one per NodeScene
class FileSceneDataProvider(ISceneDataProvider):
    plugin_manager: PluginSpecManager
    scenes_root: Path

    scene_file_reader: SceneFileReader

    def __init__(self, scene_uid: str, plugin_manager: PluginSpecManager, scenes_root: Path) -> None:
        self.scene_uid = scene_uid
        self.plugin_manager = plugin_manager
        self.scenes_root = scenes_root
        self.scene_file_reader = SceneFileReader(plugin_manager, scenes_root)

    # ISceneDataProvider

    def validate_scene_data(self, scene_data: SceneData) -> None:
        self.plugin_manager.version_manager.validate_scene_dependencies(
            scene_data.uid, scene_data.dependencies, self.plugin_manager.get_all_loaded_packages()
        )

    def save_scene_data(self, scene_data: SceneData):
        self.scene_file_reader.save_to_folder(scene_data, self.get_scene_folder(scene_data.uid))
    
    def load_scene_data(self, scene_uid: str) -> Optional[SceneData]:
        return self.scene_file_reader.load_from_folder(self.get_scene_folder(scene_uid))

    # Utils

    def get_scene_folder(self, scene_uid: str) -> Path:
        return self.scenes_root / scene_uid

class FileSceneStateProvider(ISceneStateProvider):
    _scene_uid: str
    
    def __int__(self, scene_uid: str, scenes_root: Path):
        self._scene_uid = scene_uid
        self.scenes_root = scenes_root

    def _setup_folder(self):
        self.get_scene_folder().mkdir(exist_ok=True)
        self.get_node_states_folder().mkdir(exist_ok=True)

    def _save_node_state(self, node_uid: str, node_state: LogicNodeState):
        file_path = self.get_node_state_folder(node_uid) / "node_state.json"
        file_path.write_text(node_state.model_dump_json())

    def _load_node_state(self, node_uid: str) -> LogicNodeState | None:
        file_path = self.get_node_state_folder(node_uid) / "node_state.json"
        if not file_path.exists():
            return None
        
        with open(file_path, "r") as file:
            json_str = file.read()

        try:
            return LogicNodeState.model_validate_json(json_str)
        except ValidationError as e:
            logger.error("Failed to read node state %s. file_path: %s - node_uid: %s ", str(e), file_path, node_uid)
            return None

    def get_node_state_folder(self, node_uid: str) -> Path:
        return self.get_node_states_folder() / node_uid

    def get_node_states_folder(self) -> Path:
        return self.get_scene_folder() / "node_states"
    
    def get_scene_folder(self) -> Path:
        return self.scenes_root / self._scene_uid
