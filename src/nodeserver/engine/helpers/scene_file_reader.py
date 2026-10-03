from pathlib import Path
from typing import Optional

from nodeserver.engine.plugins.plugin_spec_manager import PluginSpecManager
from nodeserver.protocols.manifest.node.node_graph import SceneData

class SceneFileReader:
    plugin_manager: PluginSpecManager # TODO: talvez trocar isso aqui por um package provider
    default_folder_path: Path

    def __init__(self, plugin_manager: PluginSpecManager, default_folder_path: Path) -> None:
        self.plugin_manager = plugin_manager
        self.default_folder_path = default_folder_path

    def load_from_file(self, file_path: Path) -> SceneData:
        with open(file_path, "r") as file:
            scene_data = SceneData.model_validate_json(file.read())

        self.plugin_manager.version_manager.validate_scene_dependencies(
            scene_data.uid, scene_data.dependencies, self.plugin_manager.get_all_loaded_packages() 
        )
        return scene_data

    def load_from_folder(self, folder_path: Optional[Path] = None) -> Optional[SceneData]:
        file_path = (folder_path or self.default_folder_path) / "graph_data.json"
        if not file_path.exists():
            return None
        
        return self.load_from_file(file_path)

    def save_to_folder(self, scene_data: SceneData, folder_path: Optional[Path] = None):
        scene_folder = folder_path or self.default_folder_path
        scene_folder.mkdir(exist_ok=True)

        file_path = scene_folder / "graph_data.json"
        file_path.write_text(scene_data.model_dump_json())
