from pathlib import Path
from typing import Optional

from nodeserver.protocols.manifest.node.node_graph import SceneData

class SceneFileReader:
    default_folder_path: Path

    def __init__(self, default_folder_path: Path) -> None:
        self.default_folder_path = default_folder_path

    def load_from_file(self, file_path: Path) -> SceneData:
        with open(file_path, "r") as file:
            scene_data = SceneData.model_validate_json(file.read())

        return scene_data

    def load_from_folder(self, folder_path: Optional[Path] = None) -> Optional[SceneData]:
        file_path = (folder_path or self.default_folder_path) / self.scene_data_filename()
        if not file_path.exists():
            return None
        
        return self.load_from_file(file_path)

    def save_to_folder(self, scene_data: SceneData, folder_path: Optional[Path] = None):
        scene_folder = folder_path or self.default_folder_path
        scene_folder.mkdir(exist_ok=True)

        file_path = scene_folder / self.scene_data_filename()
        file_path.write_text(scene_data.model_dump_json())

    @classmethod
    def scene_data_filename(cls):
        return "graph_data.json"