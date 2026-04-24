
import logging
import os
from typing import Optional
from nodeserver.api.instance.server_instance import ServerInstance
from nodeserver.api.internal.instance_state import NODE_STATE_SUBFOLDER
from nodeserver.api.internal.internal_protocols import InstanceProtocol
from nodeserver.api.utils.env_variables import WORKSPACES_PATH

logger = logging.getLogger("nds.workspace")

INSTANCE_FOLDER = "instances"
UPLOADS_FOLDER = "uploads"

class UserWorkspace:
    user_id: str
    workspace_path: str
    file_paths: list[str]
    
    instance_id: str | None = None
    current_instance: Optional[InstanceProtocol]
    
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
    
    @staticmethod
    def create(user_id: str) -> 'UserWorkspace':
        workspace = UserWorkspace(user_id)
        WorkspaceUtils.prepare_workspace(workspace) 
        
        return workspace
    
    def assign_instance(self, instance: ServerInstance):
        self.instance_id = instance._attributed_id
        self.current_instance = instance

    
    def get_instance_path(self):
        pass
    
    def save_instance(self, instance: ServerInstance):
        if instance != self.current_instance:
            logger.error(f"Saved instance should be the same as workspace's current instance - Instance Id: {instance._attributed_id} - Current Instance: {self.current_instance._attributed_id if self.current_instance else None}")
        
        instance_path, node_state_path = WorkspaceUtils.prepare_instance_path(self.workspace_path, instance._attributed_id)
        instance.save_internal_state(
            instance_path, node_state_path
        )
        
    def get_saved_instances(self) -> list[str]:
        user_instances = WorkspaceUtils.get_user_instances(self.user_id)
        user_instances.sort(key=os.path.getmtime, reverse=True)
        return user_instances
    
class WorkspaceUtils:
    @staticmethod
    def prepare_workspace(workspace: UserWorkspace) -> str:
        workspaces_path = WorkspaceUtils.prepare_workspace_path()
        user_workspace = os.path.join(workspaces_path, workspace.user_id)
        if not os.path.exists(user_workspace):
            os.mkdir(user_workspace)

        WorkspaceUtils._make_folders(
            user_workspace, [
                INSTANCE_FOLDER,
                UPLOADS_FOLDER
            ]
        )
                
        workspace.workspace_path = user_workspace
        return user_workspace
            

    @staticmethod
    def prepare_workspace_path() -> str:
        path = WORKSPACES_PATH
        if not os.path.exists(path):
            os.makedirs(path)
        
        return path
    
    @staticmethod
    def prepare_instance_path(root_path: str, instance_id: str) -> tuple[str, str]:
        instance_path: str = WorkspaceUtils.get_instance_path(root_path, instance_id)
        if not os.path.exists(instance_path):
            os.mkdir(instance_path)

        node_state_path = WorkspaceUtils.get_node_states_path(instance_path)
        if not os.path.exists(node_state_path):
            os.mkdir(node_state_path)
        
        return instance_path, node_state_path

    
    @staticmethod
    def prepare_user_instance_path(user_id: str) -> str:
        instances_folder = WorkspaceUtils.prepare_workspace_path()
        user_instances = os.path.join(instances_folder, user_id)
        os.mkdir(user_instances)

        return user_instances
    

    
    @staticmethod
    def get_instance_path(root_path: str, instance_id: str) -> str:
        return os.path.join(root_path, INSTANCE_FOLDER, instance_id)
    
    @staticmethod
    def get_node_states_path(instance_path: str) -> str:
        return os.path.join(instance_path, NODE_STATE_SUBFOLDER)


    @staticmethod
    def get_user_instances(user_id: str) -> list[str]:
        root_folder = WorkspaceUtils.prepare_workspace_path()
        user_instances_folder = os.path.join(root_folder, user_id, INSTANCE_FOLDER)
        if not os.path.exists(user_instances_folder):
            return []

        instance_directories: list[str] = []
        for filename in os.listdir(user_instances_folder):
            path = os.path.join(user_instances_folder, filename)
            if not os.path.isdir(path): continue
            instance_directories.append(path)

        return instance_directories

    @staticmethod
    def _make_folders(root_path: str, subfolders: list[str]):
        for folder in subfolders:
            folder_path = os.path.join(root_path, folder)
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)
        
