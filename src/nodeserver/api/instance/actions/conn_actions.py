from nodeserver.api.instance.actions.action_controller import Action
from nodeserver.api.internal.internal_protocols import InstanceProtocol
from nodeserver.api.web.requests.action_requests import ConnectionActionAddUpdate, ConnectionActionRemove
from nodeserver.api.web.requests.client_requests import MsgConnectionAction
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
                instance.mirror_manager.add_conn_mirror(conn_data)
            
            instance._scene.update_nodes()
            return EditorActionStatus.SUCCESSFULL

        elif isinstance(payload, ConnectionActionRemove):
            if not payload.uids:
                return EditorActionStatus.FAILED
                
            instance.mirror_manager.remove_conn_mirror(payload.uids)
            instance._scene.update_nodes()
            return EditorActionStatus.SUCCESSFULL

        return EditorActionStatus.FAILED