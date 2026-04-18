from nodeserver.api.actions.action_controller import Action
from nodeserver.api.internal.internal_protocols import InstanceProtocol
from nodeserver.api.internal.websocket_protocol import EditorActionStatus, SceneActions, ServerMessages
from nodeserver.networking.nodes.helpers.file.node_scene_dataclasses import ConnectionSceneData, NodeSceneData

class ConnActionUtils:
    @staticmethod
    def _parse_conn_action(action: Action, instance: InstanceProtocol) -> EditorActionStatus:
        if not action.message.payload:
            return EditorActionStatus.FAILED
        
        action_data = action.message.payload.get("action_data", {})
        uids: list[str] = action.message.payload.get("uids", [])
        match action.type:
            case SceneActions.ADD:
                if action_data == {}:
                    return EditorActionStatus.FAILED
                
                for conn_uid in action_data:
                    conn_data = ConnectionSceneData.from_dict(action_data[conn_uid], conn_uid)
                    connection = instance.mirror_manager.add_conn_mirror(conn_data)
                instance._scene.update_nodes()

            case SceneActions.REMOVE:
                if uids == []:
                    return EditorActionStatus.FAILED
                
                instance.mirror_manager.remove_conn_mirror(uids)
                instance._scene.update_nodes()

        return EditorActionStatus.SUCCESSFULL