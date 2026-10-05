from pathlib import Path
import logging

from nodeserver.engine.helpers.scene_file_reader import SceneFileReader
from nodeserver.protocols.manifest.node.node_graph import SceneData
from nodeserver.server.protocols.permission.scene_permissions import ScenePermission
from nodeserver.server.protocols.providers.scene_provider_protocol import IServerSceneProvider
from nodeserver.server.protocols.scene_list_protocol import ListedScene, ListedScenePerms

logger = logging.getLogger("nds.server")

class SceneProvider(IServerSceneProvider):
    scenes_root: Path

    def __init__(self, scenes_root: Path) -> None:
        self.scenes_root = scenes_root
    
    def setup(self):
        pass

    # IServerSceneProvider

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

    def get_scene_permissions(self, scene_uid: str, user_id: str) -> ScenePermission: 
        perms = self._load_or_create_scene_permissions(scene_uid)
        return perms.user_permissions.get(user_id, perms.default_perm)

    def update_scene_permissions(self, scene_uid: str, user_id: str, permissions: ScenePermission):
        perms = self._load_or_create_scene_permissions(scene_uid)
        perms.user_permissions[user_id] = permissions

        perms_file = self.get_scene_perms_file(scene_uid)
        perms_file.write_text(perms.model_dump_json())

    # Utils:
    
    def _load_or_create_scene_permissions(self, scene_uid: str) -> ListedScenePerms:
        perms_file = self.get_scene_perms_file(scene_uid)
        perms = ListedScenePerms(default_perm=ScenePermission.VIEWER)
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
    