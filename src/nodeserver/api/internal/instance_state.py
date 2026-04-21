import os
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel
import logging

from nodeserver.api.utils.env_variables import INSTANCE_STATE_PATH
from nodeserver.wrapper.nodes.helpers.file.node_scene_dataclasses import NodeSceneData, SceneData
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
    def prepare_state_path() -> str:
        path = INSTANCE_STATE_PATH
        if not os.path.exists(path):
            os.makedirs(path)
        
        return path
    
    @staticmethod
    def prepare_instance_path(root_path: str, instance_id: str) -> tuple[str, str]:
        instance_path: str = StateFileUtils.get_instance_path(root_path, instance_id)
        if not os.path.exists(instance_path):
            os.mkdir(instance_path)

        node_state_path = StateFileUtils.get_node_states_path(instance_path)
        os.mkdir(node_state_path)
        return instance_path, node_state_path
    
    @staticmethod
    def get_instance_path(root_path: str, instance_id: str) -> str:
        return os.path.join(root_path, instance_id)
    
    @staticmethod
    def get_node_states_path(instance_path: str) -> str:
        return os.path.join(instance_path, NODE_STATE_SUBFOLDER)

    @staticmethod
    def prepare_user_instance_path(user_id: str) -> str:
        instances_folder = StateFileUtils.prepare_state_path()
        user_instances = os.path.join(instances_folder, user_id)
        os.mkdir(user_instances)

        return user_instances

    @staticmethod
    def save_instance_state(state: InstanceState, instance_path: str):
        state_file_path = os.path.join(instance_path, "instance_state.json")
        with open(state_file_path, "w+") as file:
            file.write(state.model_dump_json(indent=1))

        for node_state in state.internal_states.nodes:
            pass

    @staticmethod
    def get_user_instances(user_id: str) -> list[str]:
        root_folder = StateFileUtils.prepare_state_path()
        user_folder = os.path.join(root_folder, user_id)
        if not os.path.exists(user_folder):
            return []

        instance_directories: list[str] = []
        for filename in os.listdir(user_folder):
            path = os.path.join(user_folder, filename)
            if not os.path.isdir(path): continue
            instance_directories.append(path)

        return instance_directories

    @staticmethod
    def get_user_recent_instance_state(user_id: str) -> Optional[tuple[str, Optional[InstanceState]]]:
        user_instances = StateFileUtils.get_user_instances(user_id)
        # Instance Path is the same as Instance Id
        if len(user_instances) == 0: return

        user_instances.sort(key=os.path.getmtime, reverse=True)
        state_root = user_instances[0]
        state = StateFileUtils.get_instance_state(state_root)
        return state_root, state

    @staticmethod
    def get_instance_state(instance_path: str) -> Optional[InstanceState]:
        state_file_path = os.path.join(instance_path, "instance_state.json")
        if not os.path.exists(state_file_path):
            logger.error(f"Instance Folder exists, but state file doesn't. Path: {instance_path}")
            return
        
        json_data = Path(state_file_path).read_text()
        state_data = InstanceState.model_validate_json(json_data)

        return state_data
