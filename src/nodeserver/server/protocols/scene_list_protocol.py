from pydantic import BaseModel, Field, field_validator, model_validator

from nodeserver.server.protocols.permission.scene_permissions import ScenePermission


class ListedScene(BaseModel):
    uid: str
    dependencies: dict[str, str]

class ListedScenePerms(BaseModel):
    # user_id -> perms
    user_permissions: dict[str, ScenePermission] = Field(default_factory=dict)
    default_perm: ScenePermission
