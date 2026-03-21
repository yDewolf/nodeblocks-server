from __future__ import annotations
import json
from nodeserver.networking.nodes.helpers.file.node_scene_dataclasses import SceneData


class SceneFile:
    _virtual_file: SceneFile | None = None

    raw_data: dict | None = None
    scene_data: SceneData | None = None

    def __init__(self, is_virtual: bool = False) -> None:
        if not is_virtual:
            self._virtual_file = SceneFile(True)
    

    # TODO:
    def save_to_file(self, data: SceneData):
        pass

    
    def is_virtual_data_compatible(self) -> bool: 
        if self.scene_data == None:
            return True
        
        if self._virtual_file == None:
            return False
        
        if self._virtual_file.scene_data == None:
            return False

        virtual_data = self._virtual_file.scene_data
        if virtual_data.node_types_id != self.scene_data.node_types_id:
            return False
        
        if virtual_data.node_types_version != self.scene_data.node_types_version:
            return False

        return False
    
    def swap_virtual_data(self):
        if self._virtual_file == None:
            return False
        
        if self._virtual_file.scene_data == None:
            return False

        self.scene_data = self._virtual_file.scene_data
        self.raw_data = self._virtual_file.raw_data

        self._virtual_file = SceneFile(True)


    def load_from_file(self, file_path: str):
        with open(file_path, "r") as file:
            json_data = json.load(file)
            self._load_json_data(json_data)


    def _load_json_data(self, json_data: dict):
        if not self._virtual_file:
            return
        
        scene_data = SceneData.from_dict(json_data)
        self._virtual_file.scene_data = scene_data
        self._virtual_file.raw_data = json_data