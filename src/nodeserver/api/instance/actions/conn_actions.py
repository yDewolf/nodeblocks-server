from nodeserver.api.instance.actions.action_controller import Action
from nodeserver.api.internal.internal_protocols import InstanceProtocol
from nodeserver.api.node.node_exceptions import ReachedMaxConnections
from nodeserver.api.web.requests.action_requests import ConnectionActionAddUpdate, ConnectionActionRemove
from nodeserver.api.web.requests.client_requests import MsgConnectionAction
from nodeserver.api.web.requests.notification_requests import NotificationLevel, ServerNotification
from nodeserver.api.web.websocket_protocol import EditorActionStatus

class ConnActionUtils:
    @staticmethod
    def _parse_conn_action(action: Action, instance: InstanceProtocol) -> EditorActionStatus:
        msg = action.message.msg
        if not isinstance(msg, MsgConnectionAction):
            return EditorActionStatus.FAILED
        
        payload = msg.payload
        if isinstance(payload, ConnectionActionAddUpdate):
            for conn_uid, conn_data in payload.action_data.items():
                conn_data.uid = conn_uid
                try:
                    conn = instance.mirror_manager.add_conn_mirror(conn_data)
                    if not conn:
                        instance.send_to_client(ServerNotification.conn_notify(
                            conn_uid=conn_uid,
                            message="Failed to add connection",
                            level=NotificationLevel.WARNING
                        ))
                        continue
                except ReachedMaxConnections as e:
                    instance.send_to_client(ServerNotification.slot_notify(
                        node_uid=e.slot.parent_node.uid,                        
                        slot_name=e.slot.slot_name,
                        message="Slot reached Max Connections",
                        level=NotificationLevel.ERROR
                    ))
                    continue

                instance.send_to_client(ServerNotification.conn_notify(
                    conn_uid=conn_uid,
                    message="Added connection",
                    level=NotificationLevel.DEBUG
                ))

            instance._scene.update_nodes()
            return EditorActionStatus.SUCCESSFULL

        elif isinstance(payload, ConnectionActionRemove):
            if not payload.uids:
                return EditorActionStatus.FAILED
            
            instance.mirror_manager.remove_conn_mirror(payload.uids)
            instance._scene.update_nodes()
            return EditorActionStatus.SUCCESSFULL

        return EditorActionStatus.FAILED