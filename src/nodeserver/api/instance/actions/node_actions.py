from nodeserver.api.instance.actions.action_controller import Action
from nodeserver.api.instance.base_nodes import BaseNode
from nodeserver.api.internal.internal_protocols import InstanceProtocol
from nodeserver.api.web.requests.action_requests import NodeActionAddUpdate, NodeActionRemove
from nodeserver.api.web.requests.client_requests import MsgNodeAction
from nodeserver.api.web.requests.notification_requests import NotificationLevel, ServerNotification
from nodeserver.api.web.websocket_protocol import EditorActionStatus, SceneActionTypes

class NodeActionUtils:
    @staticmethod
    def _parse_node_action(action: Action, instance: InstanceProtocol) -> EditorActionStatus:
        msg = action.message.msg
        if not isinstance(msg, MsgNodeAction):
            return EditorActionStatus.FAILED
        
        payload = msg.payload
        if isinstance(payload, NodeActionAddUpdate):
            # Node Update
            if action.type == SceneActionTypes.UPDATE:
                return NodeActionUtils._node_update(payload, instance)
            
            # Node Add
            return NodeActionUtils._node_add(payload, instance)

        elif isinstance(payload, NodeActionRemove):
            instance.mirror_manager.remove_node_mirrors(payload.uids)
            instance._scene.update_nodes()
            return EditorActionStatus.SUCCESSFULL

        return EditorActionStatus.FAILED
    

    @staticmethod
    def _node_update(payload: NodeActionAddUpdate, instance: InstanceProtocol) -> EditorActionStatus:
        for node_uid, node_data in payload.action_data.items():
            node_data.uid = node_uid
            mirror = instance.mirror_manager.node_manager.get_node(node_uid)
            if not mirror:
                return EditorActionStatus.FAILED

            mirror._position = node_data.position
            for param_name in node_data.data:
                mirror.data.set_parameter_value(param_name, node_data.data.get(param_name))
        
            if instance.mirror_manager.scene_reader.scene_data:
                instance.mirror_manager.scene_reader.sync_node(mirror)

        return EditorActionStatus.SUCCESSFULL
    
    @staticmethod
    def _node_add(payload: NodeActionAddUpdate, instance: InstanceProtocol) -> EditorActionStatus:
        nodes: list[BaseNode] = []
        for node_uid, node_data in payload.action_data.items():
            node_data.uid = node_uid
            mirror = instance.mirror_manager.add_node_mirror(node_data, node_uid)
            if not mirror:
                return EditorActionStatus.FAILED
            
            node = instance._scene.build_node(mirror)
            if node:
                nodes.append(node)

        # FIXME
        for node in nodes:
            is_fine = node.self_validate(instance._scene.mirror_manager.node_manager, instance._scene.mirror_manager.connection_manager)
            if not is_fine:
                instance.send_to_client(ServerNotification.node_notify(
                    message="Something went wrong with this guy idk",
                    level=NotificationLevel.ERROR,
                    node_uid=node._mirror.uid
                ))
                continue

            instance.send_to_client(ServerNotification.node_notify(
                node._mirror.uid,
                message=f"Added node of type {node._mirror.type_name}",
                level=NotificationLevel.DEBUG
            ))

        instance._scene.add_nodes(nodes)
        instance._scene.update_nodes()
        return EditorActionStatus.SUCCESSFULL