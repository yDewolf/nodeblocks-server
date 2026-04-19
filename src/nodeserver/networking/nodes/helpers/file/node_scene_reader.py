from __future__ import annotations
import json
from nodeserver.networking.nodes.helpers.file.node_scene_dataclasses import SceneData
from nodeserver.networking.utils.uuid_utils import IDGenerator


class SceneFileReader:
    _virtual_file: SceneFileReader | None = None

    raw_data: dict | None = None
    scene_data: SceneData | None = None

    def __init__(self, is_virtual: bool = False) -> None:
        if not is_virtual:
            self._virtual_file = SceneFileReader(True)


    def new_scene(self, node_types_id: str, node_types_version: int):
        self.scene_data = SceneData(
            uid=IDGenerator.generate_id(),
            node_types_id=node_types_id,
            node_types_version=node_types_version,
            nodes={}, connections={}
        )

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

        return True
    
    def swap_virtual_data(self):
        if self._virtual_file == None:
            return False
        
        if self._virtual_file.scene_data == None:
            return False

        self.scene_data = self._virtual_file.scene_data
        self.raw_data = self._virtual_file.raw_data

        self._virtual_file = SceneFileReader(True)


    def load_from_file(self, file_path: str):
        with open(file_path, "r") as file:
            json_data = json.load(file)
            self._load_json_data(json_data)


    def _load_json_data(self, json_data: dict| SceneData):
        if not self._virtual_file:
            return
        
        if isinstance(json_data, SceneData):
            self._virtual_file.scene_data = json_data
            self._virtual_file.raw_data = json_data.serialize()
            return
        scene_data = SceneData.from_dict(json_data)
        self._virtual_file.scene_data = scene_data
        self._virtual_file.raw_data = json_data