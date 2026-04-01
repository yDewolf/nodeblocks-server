from enum import Enum
import json

from nodeserver.api.instance_states import InstanceCommands, InstanceStates, LoopStates
from nodeserver.api.server_instance import ServerInstance
from nodeserver.networking.nodes.helpers.file.node_scene_dataclasses import ConnectionSceneData, NodeSceneData

class SceneActions(Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"
    UPDATE = "UPDATE"

class BaseCommandRouter:
    def route_message(self, msg_type: str, payload: dict, instance: ServerInstance) -> dict | None:
        # TODO: Simplify this if return mess
        out = self._route_utility_commands(msg_type, payload, instance)
        if out != None: return out
        
        out = self._route_state_setters(msg_type, payload, instance)
        if out != None: return out
        
        out = self._route_state_commands(msg_type, payload, instance)
        if out != None: return out

        out = self._route_scene_commands(msg_type, payload, instance)
        if out != None: return out


    @staticmethod
    def _route_utility_commands(msg_type: str, payload: dict, instance: ServerInstance) -> dict |  None:
        match msg_type.upper():
            case "GET_TYPES":
                return {"type": msg_type, "payload": json.dumps(instance.mirror_manager.type_reader.serialize_to_dict())}

    @staticmethod
    def _route_state_commands(msg_type: str, payload: dict, instance: ServerInstance):
        match msg_type.upper():
            case "RUN":
                instance.start_running()
            case "RESUME":
                instance.state_controller.command_queue.put(InstanceCommands.RESUME_LOOP)
            case "STOP":
                instance.state_controller.command_queue.put(InstanceCommands.STOP)
            case "STEP":
                instance.state_controller.command_queue.put(InstanceCommands.STEP_NEXT)


    @staticmethod
    def _route_state_setters(msg_type: str, payload: dict, instance: ServerInstance):
        match msg_type.upper():
            case "SET_STATE":
                try:
                    new_state = InstanceStates(payload.get("state", -1))
                    instance.state_controller.queue_state(new_state)
                except ValueError:
                    pass

            case "SET_LOOP_STATE":
                try:
                    new_state = LoopStates(payload.get("state", -1))
                    instance.state_controller.queue_loop_state(new_state)
                except ValueError:
                    pass
    
    
    def _route_scene_commands(self, msg_type: str, payload: dict, instance: ServerInstance):
        match msg_type.upper():
            case "LOAD_SCENE":
                # FIXME is the payload supposed to be the full scene?
                instance.load_new_scene(payload)
                return
        
        uid = payload.get("uid", None)
        action = payload.get("action", None)
        if not uid or not action:
            return
        
        try:
            action_type = SceneActions(str(action).upper())
            match msg_type.upper():
                case "NODE":
                    self._parse_node_commands(uid, action_type, payload, instance)
                    return

                case "CONNECTION":
                    self._parse_conn_commands(uid, action_type, payload, instance)
                    return
        
        except ValueError:
            # TODO: Handle Error
            pass

    @staticmethod
    def _parse_node_commands(node_uid: str, action: SceneActions, payload: dict, instance: ServerInstance):
        match action:
            case SceneActions.ADD:
                node_data = NodeSceneData.from_dict(payload, node_uid)
                mirror = instance.mirror_manager.add_node_mirror(node_data, node_data.id)
                
                if not mirror:
                    return
                
                node = instance._scene.build_node(mirror)
                if node:
                    instance._scene.add_node(node)

            case SceneActions.REMOVE:
                instance.mirror_manager.remove_node_mirror(node_uid)
                instance._scene.update_nodes()

    @staticmethod
    def _parse_conn_commands(conn_uid: str, action: SceneActions, payload: dict, instance: ServerInstance):
        match action:
            case SceneActions.ADD:
                conn_data = ConnectionSceneData.from_dict(payload, conn_uid)
                connection = instance.mirror_manager.add_conn_mirror(conn_data)

            case SceneActions.REMOVE:
                instance.mirror_manager.remove_conn_mirror(conn_uid)
                instance._scene.update_nodes()