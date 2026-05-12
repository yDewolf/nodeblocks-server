from __future__ import annotations

import datetime
import logging
import os
from typing import Optional
from nodeserver.api.instance.server_instance import ServerInstance
from nodeserver.api.utils.workspace_utils import INSTANCE_FOLDER, UPLOADS_FOLDER, WorkspaceUtils
from nodeserver.api.web.requests.notification_requests import NotificationLevel, ServerNotification
from nodeserver.api.web.requests.request_unions import AnyServerMessage
from nodeserver.api.web.session.user_notifications import NotificationController

logger = logging.getLogger("nds.workspace")

class UserWorkspace:
    user_id: str
    workspace_path: str
    file_paths: list[str]
    
    instance_id: str | None = None
    current_instance: Optional[ServerInstance]

    notification_controller: NotificationController
    
    _autosave_interval: datetime.timedelta = datetime.timedelta(minutes=3)
    _last_autosave: Optional[datetime.datetime] = None

    @property
    def last_autosave(self): return self._last_autosave

    @property
    def autosave_interval(self): return self._autosave_interval


    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.notification_controller = NotificationController()

    @staticmethod
    def create(user_id: str) -> 'UserWorkspace':
        workspace = UserWorkspace(user_id)
        workspace.workspace_path = WorkspaceUtils.prepare_workspace(workspace)
        
        return workspace
    
    def assign_instance(self, instance: ServerInstance):
        self.instance_id = instance._attributed_id
        self.current_instance = instance
        self.notification_controller.instance = self.current_instance

    def send_msg_as_instance(self, data: AnyServerMessage) -> bool:
        if not self.current_instance:
            return False

        self.current_instance.send_to_client(data)
        return True

    
    def get_instance_path(self):
        pass

    def get_uploads_path(self):
        return WorkspaceUtils.get_user_uploads_path(self.workspace_path)


    # Autosaves if it should autosave
    def do_autosave(self):
        if not self.check_autosave():
            return
        
        if not self.current_instance:
            return
        
        self.send_msg_as_instance(ServerNotification.notify(
            message="Saving instance...",
            level=NotificationLevel.WARNING
        ))

        self.save_instance(self.current_instance)

    def check_autosave(self) -> bool:
        if not self.last_autosave:
            return True
        
        if self.last_autosave + self.autosave_interval < datetime.datetime.now(datetime.timezone.utc):
            return True
        
        return False

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
