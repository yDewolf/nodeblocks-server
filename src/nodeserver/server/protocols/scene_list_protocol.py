from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from nodeserver.server.protocols.permission.scene_permissions import ScenePermission


class ListedScene(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    uid: str
    dependencies: dict[str, str]
    user_perms: Optional[ScenePermission] = Field(default=None)

class ListedScenePerms(BaseModel):
    # user_id -> perms
    user_permissions: dict[str, ScenePermission] = Field(default_factory=dict)
    default_perm: ScenePermission
