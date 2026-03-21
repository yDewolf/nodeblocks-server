from nodeserver.networking.nodes.helpers.file.node_scene_reader import SceneFile
from nodeserver.networking.nodes.helpers.file.typing_file_reader import TypingFile
from test_data import SCENE_DATA_JSON, TYPE_FILE_JSON

types_file = TypingFile()
types_file._load_json_data(
    TYPE_FILE_JSON
)

scene_file = SceneFile()
scene_file._load_json_data(SCENE_DATA_JSON)
if scene_file._virtual_file:
    scene_data = scene_file._virtual_file.scene_data

    if scene_data:
        assert types_file.is_scene_compatible(scene_data)

pass