
from typing import Optional

from nodeserver.api.internal.internal_protocols import InstanceProtocol
from nodeserver.api.web.requests.notification_requests import NotificationWithMeta, ServerNotification


class NotificationController:
    instance: Optional[InstanceProtocol]
    unread_notifications: dict[str, ServerNotification]

    def __init__(self) -> None:
        self.unread_notifications = {}

    def add_notification(self, notification: ServerNotification):
        if not self.unread_notifications.__contains__(notification.uid):
            self.unread_notifications[notification.uid] = notification
    
    def _mark_as_read(self, notification_uid: str):
        self.unread_notifications.pop(notification_uid, None)


    def get_unread_notifications(self) -> list[ServerNotification]:
        return list(self.unread_notifications.values())


    def update_notification(self, msg_payload: NotificationWithMeta):
        if msg_payload.read:
            self._mark_as_read(msg_payload.uid)