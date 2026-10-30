from pydantic import BaseModel, ConfigDict, Field

from nodeserver.server.protocols.permission.scene_permissions import ScenePermission

# TODO: make these inherit a AuthenticatedRequest model 
class UpdateScenePermsModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    user_id: str # Logged User

    user_perms: ScenePermission

class CreateSceneModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    user_id: str
    scene_id: str

    default_perm: ScenePermission = Field(default=ScenePermission.NONE)

