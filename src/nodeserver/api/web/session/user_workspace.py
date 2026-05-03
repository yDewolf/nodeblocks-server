from __future__ import annotations

import logging
import os
from typing import Optional
from nodeserver.api.instance.server_instance import ServerInstance
from nodeserver.api.internal.internal_protocols import InstanceProtocol
from nodeserver.api.utils.workspace_utils import INSTANCE_FOLDER, UPLOADS_FOLDER, WorkspaceUtils
from nodeserver.api.web.requests.websocket_requests import ServerMessage

logger = logging.getLogger("nds.workspace")

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
        workspace.workspace_path = WorkspaceUtils.prepare_workspace(workspace)
        
        return workspace
    
    def assign_instance(self, instance: ServerInstance):
        self.instance_id = instance._attributed_id
        self.current_instance = instance

    def send_msg_as_instance(self, data: ServerMessage) -> bool:
        if not self.current_instance:
            return False

        self.current_instance.send_to_client(data)
        return True

    
    def get_instance_path(self):
        pass

    def get_uploads_path(self):
        return WorkspaceUtils.get_user_uploads_path(self.workspace_path)


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
