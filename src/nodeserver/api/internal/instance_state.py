import os
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel
import logging

from nodeserver.wrapper.nodes.helpers.file.node_scene_dataclasses import SceneData
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import TypeFile

logger = logging.getLogger("nds.state_file")

NODE_STATE_SUBFOLDER = "node_states"

class InternalNodeState(BaseModel):
    # Relative to NODE_STATE_SUBFOLDER inside instance's folder
    relative_state_path: Optional[str] # node.save_state() can return a path to some file that stores node's state
    state_data: Optional[dict[str, Any]] # if the node doesn't save in an external file, it should use this state_data
    # Other node data


class InternalState(BaseModel):
    nodes: dict[str, InternalNodeState]

class InstanceState(BaseModel):
    instance_id: str
    user_id: str
    instance_creation_time: float

    instance_version: str

    scene_data: SceneData
    types_data: TypeFile # So it can check if current interpreter matches the original types
    
    internal_states: InternalState


class StateFileUtils:
    @staticmethod
    def save_instance_state(state: InstanceState, instance_path: str):
        state_file_path = os.path.join(instance_path, "instance_state.json")
        with open(state_file_path, "w+") as file:
            file.write(state.model_dump_json(indent=1))

        # for node_state in state.internal_states.nodes:
        #     pass

    @staticmethod
    def get_instance_state(instance_path: str) -> Optional[InstanceState]:
        state_file_path = os.path.join(instance_path, "instance_state.json")
        if not os.path.exists(state_file_path):
            logger.error(f"Instance Folder exists, but state file doesn't. Path: {instance_path}")
            return
        
        json_data = Path(state_file_path).read_text()
        state_data = InstanceState.model_validate_json(json_data)

        return state_data
