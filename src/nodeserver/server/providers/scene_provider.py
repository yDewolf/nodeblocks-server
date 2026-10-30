from pathlib import Path
import logging
from typing import Optional

from nodeserver.engine.helpers.scene_file_reader import SceneFileReader
from nodeserver.protocols.manifest.node.node_graph import SceneData
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.providers.scene_provider_protocol import IServerSceneProvider
from nodeserver.server.protocols.scene_list_protocol import ListedScene, ListedScenePerms

logger = logging.getLogger("nds.server")

class SceneProvider(IServerSceneProvider):
    scenes_root: Path
    file_reader: SceneFileReader

    def __init__(self, scenes_root: Path) -> None:
        self.scenes_root = scenes_root
        self.file_reader = SceneFileReader(scenes_root)
    
    def setup(self):
        pass

    # IServerSceneProvider

    def create_scene(self, scene_id: str, author_id: str, default_perms: ScenePermission):
        scene_folder = self.get_scene_folder(scene_id)
        if scene_folder.exists():
            raise Exception("A scene with the same id already exists")
        
        scene_folder.mkdir()
        self._load_or_create_scene_permissions(scene_id, perms=ListedScenePerms(
            user_permissions={author_id: ScenePermission.ALL},
            default_perm=default_perms
        ))
        self.save_scene_data(SceneData(uid=scene_id, dependencies={}))

    # TODO: intercept scene creation so we can cache scenes inside a .json file
    # or something like that
    def get_listed_scenes(self) -> list[ListedScene]:
        listed_scenes: list[ListedScene] = []
        for subpath in self.scenes_root.iterdir():
            if not subpath.is_dir():
                continue

            file_path = subpath / SceneFileReader.scene_data_filename()
            if not file_path.exists():
                continue

            with open(file_path, "r") as file:
                scene_data = SceneData.model_validate_json(file.read())
                listed_scenes.append(ListedScene(
                    uid=scene_data.uid,
                    dependencies=scene_data.dependencies
                ))

        return listed_scenes

    def get_default_scene_perms(self, scene_uid: str) -> ScenePermission:
        perms = self._load_or_create_scene_permissions(scene_uid)
        return perms.default_perm

    def get_all_scene_perms(self, scene_uid: str) -> ListedScenePerms:
        perms = self._load_or_create_scene_permissions(scene_uid)
        return perms

    def get_scene_permissions(self, scene_uid: str, user_id: str) -> ScenePermission: 
        perms = self._load_or_create_scene_permissions(scene_uid)
        return perms.user_permissions.get(user_id, perms.default_perm)

    def update_scene_permissions(self, scene_uid: str, permissions: ScenePermission, user_id: Optional[str] = None):
        perms = self._load_or_create_scene_permissions(scene_uid)
        if user_id:
            perms.user_permissions[user_id] = permissions
        else:
            perms.default_perm = permissions

        perms_file = self.get_scene_perms_file(scene_uid)
        perms_file.write_text(perms.model_dump_json())

    # Loader stuff:

    def load_scene_data(self, scene_uid: str) -> SceneData | None:
        return self.file_reader.load_from_folder(self.scenes_root / scene_uid)

    def save_scene_data(self, scene_data: SceneData):
        return self.file_reader.save_to_folder(scene_data, self.scenes_root / scene_data.uid)

    # Utils:
    
    def _load_or_create_scene_permissions(self, scene_uid: str, perms: Optional[ListedScenePerms] = None) -> ListedScenePerms:
        perms_file = self.get_scene_perms_file(scene_uid)
        perms = perms or ListedScenePerms(default_perm=ScenePermission.VIEWER)
        if perms_file.exists():
            try:
                with open(perms_file, "r") as file:
                    perms = ListedScenePerms.model_validate_json(file.read())
            except Exception as e:
                logger.error("Failed to read permissions for scene: %s - File Path: %s", scene_uid, perms_file)
        else:
            perms_file.write_text(perms.model_dump_json())

        return perms

    # Utils:

    def get_scene_perms_file(self, scene_uid: str) -> Path:
        return self.get_scene_folder(scene_uid) / "perms.json"


    def get_scene_folder(self, scene_uid: str) -> Path:
        return self.scenes_root / scene_uid
    