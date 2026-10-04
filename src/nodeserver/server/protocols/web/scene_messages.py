from pydantic import BaseModel, ConfigDict, field_serializer

from nodeserver.server.protocols.permission.scene_permissions import ScenePermission


class GetScenePermsModel(BaseModel):
    user_id: str

class UpdateScenePermsModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    user_id: str # Logged User

    target_user_id: str
    user_perms: ScenePermission
