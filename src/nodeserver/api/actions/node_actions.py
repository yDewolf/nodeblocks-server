from nodeserver.api.actions.action_controller import Action
from nodeserver.api.base_nodes import BaseNode
from nodeserver.api.internal.internal_protocols import InstanceProtocol
from nodeserver.api.internal.websocket_protocol import EditorActionStatus, SceneActions
from nodeserver.networking.nodes.helpers.file.node_scene_dataclasses import NodeSceneData

class NodeActionUtils:
    @staticmethod
    def _parse_node_action(action: Action, instance: InstanceProtocol) -> EditorActionStatus:
        if not action.message.payload:
            return EditorActionStatus.FAILED
        
        action_data = action.message.payload.get("action_data", {})
        uids: list[str] = action.message.payload.get("uids", [])
        match action.type:
            case SceneActions.ADD:
                if action_data == {}:
                    return EditorActionStatus.FAILED
                
                nodes: list[BaseNode] = []
                for node_uid in action_data:
                    node_data = NodeSceneData.from_dict(action_data[node_uid], uid=node_uid)
                    mirror = instance.mirror_manager.add_node_mirror(node_data, node_data.uid)
                    if not mirror:
                        # FIXME: Should I just continue?
                        return EditorActionStatus.FAILED
                    
                    node = instance._scene.build_node(mirror)
                    if node:
                        nodes.append(node)

                instance._scene.add_nodes(nodes)
                instance._scene.update_nodes()

            case SceneActions.REMOVE:
                instance.mirror_manager.remove_node_mirrors(uids)
                instance._scene.update_nodes()

            # FIXME: Make some Update Node Parameter function
            case SceneActions.UPDATE:
                if action_data == {}:
                    return EditorActionStatus.FAILED
                
                for node_uid in action_data:
                    node_data = action_data[node_uid]
                    mirror = instance.mirror_manager.node_manager.get_node(node_uid)
                    if not mirror:
                        # FIXME: Should I just continue?
                        return EditorActionStatus.FAILED

                    for param_name in node_data.get("data", {}):
                        parameter = mirror.data.parameters.get(param_name)
                        if not parameter:
                            continue
                        
                        parameter.value = node_data["data"][param_name]
                    
                    if instance.mirror_manager.scene_reader.scene_data:
                        instance.mirror_manager.scene_reader.scene_data.nodes[node_uid].data = mirror.data.map_parameters()
        
        return EditorActionStatus.SUCCESSFULL