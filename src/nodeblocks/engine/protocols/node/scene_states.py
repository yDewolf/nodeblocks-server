from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel


class LogicNodeState(BaseModel):
    """
        Should be relative to node state folder (see ISceneStateProvider.get_node_states_folder)
        Should be set in BaseNode.save_state(...)
    """
    extra_files: Optional[dict[str, Path]] = None
    state_data: Optional[dict[str, Any]] = None

class SceneState(BaseModel):
    node_states: dict[str, LogicNodeState]

