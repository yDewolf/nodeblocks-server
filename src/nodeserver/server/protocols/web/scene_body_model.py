from pydantic import BaseModel, ConfigDict

from nodeserver.server.protocols.permission.scene_permissions import ScenePermission

class UpdateScenePermsModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    user_id: str # Logged User

    target_user_id: str
    user_perms: ScenePermission
