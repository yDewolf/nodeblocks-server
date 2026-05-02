from enum import Enum
from typing import Any, Literal, Optional

from pydantic import model_validator

from nodeserver.api.web.requests.base_requests import BaseSocketModel
from nodeserver.api.web.websocket_protocol import ServerMessages
from nodeserver.wrapper.utils.uuid_utils import IDGenerator

class NotificationLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"

class NotificationTarget(str, Enum):
    NODE = "node"
    SLOT = "slot"
    PARAMETER = "param"

    CONNECTION = "conn"
    UNSPECIFIED = "unspecified"

class ServerNotification(BaseSocketModel):
    type: Literal[ServerMessages.NOTIFICATION] = ServerMessages.NOTIFICATION
    uid: str
    target: NotificationTarget = NotificationTarget.UNSPECIFIED
    level: NotificationLevel

    message: str 
    extra_data: Optional[dict[str, Any]] = None
    node_uid: Optional[str] = None
    slot_name: Optional[str] = None
    param_name: Optional[str] = None
    conn_uid: Optional[str] = None

    @classmethod 
    def notify(cls, message: str, level: NotificationLevel, target: NotificationTarget = NotificationTarget.UNSPECIFIED, extra_data: Optional[dict[str, Any]] = None, **kwargs):
        return cls(uid=IDGenerator.generate_notification_uid(),
            level=level, target=target, message=message, extra_data=extra_data, **kwargs
        )

    @classmethod 
    def node_notify(cls, node_uid: str, message: str, level: NotificationLevel, extra_data: Optional[dict[str, Any]] = None):
        return cls.notify(message, level, NotificationTarget.NODE, extra_data=extra_data, 
            node_uid=node_uid
        )
    
    @classmethod 
    def slot_notify(cls, node_uid: str, slot_name: str, message: str, level: NotificationLevel, extra_data: Optional[dict[str, Any]] = None):
        return cls.notify(message, level, NotificationTarget.SLOT, extra_data=extra_data, 
            node_uid=node_uid, slot_name=slot_name
        )
    
    @classmethod 
    def conn_notify(cls, conn_uid: str, message: str, level: NotificationLevel, extra_data: Optional[dict[str, Any]] = None):
        return cls.notify(message, level, NotificationTarget.CONNECTION, extra_data=extra_data, 
            conn_uid=conn_uid
        )
    
    @classmethod 
    def param_notify(cls, node_uid: str, param_name: str, message: str, level: NotificationLevel, extra_data: Optional[dict[str, Any]] = None):
        return cls.notify(message, level, NotificationTarget.PARAMETER, extra_data=extra_data, 
            node_uid=node_uid, param_name=param_name
        )

    @model_validator(mode='after')
    def check_targets(self):
        if self.target == NotificationTarget.SLOT:
            if not self.node_uid or not self.slot_name:
                raise ValueError("Slot notifications require node_uid and slot_name")
        
        elif self.target == NotificationTarget.PARAMETER:
            if not self.node_uid or not self.param_name:
                raise ValueError("Parameter notifications require node_uid and param_name")

        elif self.target == NotificationTarget.NODE:
            if not self.node_uid:
                raise ValueError("Node notifications require node_uid")

        elif self.target == NotificationTarget.CONNECTION:
            if not self.conn_uid:
                raise ValueError("Connection notifications require conn_uid")

        return self

class ServerSyncNotifications(BaseSocketModel):
    type: Literal[ServerMessages.SYNC_NOTIFICATIONS] = ServerMessages.SYNC_NOTIFICATIONS
    notifications: list[ServerNotification]
