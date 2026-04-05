from enum import Enum
import json
import logging

from nodeserver.api.instance_states import InstanceCommands, InstanceStates, LoopStates
from nodeserver.api.internal.websocket_protocol import ClientMessages, SceneActions, ServerMessages
from nodeserver.api.server_instance import ServerInstance
from nodeserver.networking.nodes.helpers.file.node_scene_dataclasses import ConnectionSceneData, NodeSceneData

COMMAND_LOGGER = logging.getLogger("nds.commands")

class BaseCommandRouter:
    def route_message(self, msg_type: str, payload: dict, instance: ServerInstance) -> dict | None:
        # TODO: Simplify this if return mess
        COMMAND_LOGGER.info(f"Routing command for instance {instance._attributed_id} type: {msg_type} | Payload: {payload}")
        try:
            parsed_msg_type = ClientMessages(msg_type.upper())
            out = self._route_utility_commands(parsed_msg_type, payload, instance)
            if out != None: return out
            
            out = self._route_state_setters(parsed_msg_type, payload, instance)
            if out != None: return out
            
            out = self._route_state_commands(parsed_msg_type, payload, instance)
            if out != None: return out

            out = self._route_scene_commands(parsed_msg_type, payload, instance)
            if out != None: return out
        
        except ValueError as e:
            pass


    @staticmethod
    def _route_utility_commands(msg_type: ClientMessages, payload: dict, instance: ServerInstance) -> dict |  None:
        match msg_type:
            case ClientMessages.GET_TYPES:
                return {"type": msg_type, "payload": json.dumps(instance.mirror_manager.type_reader.serialize_to_dict())}

    @staticmethod
    def _route_state_commands(msg_type: ClientMessages, payload: dict, instance: ServerInstance):
        if msg_type != ClientMessages.INSTANCE_COMMAND:
            return
        
        try:
            command = InstanceCommands(payload.get("action", "").upper())
            match command:
                case InstanceCommands.RUN:
                    instance.start_running()
                case InstanceCommands.RESUME:
                    instance.state_controller.command_queue.put(InstanceCommands.RESUME)
                case InstanceCommands.STOP:
                    instance.state_controller.command_queue.put(InstanceCommands.STOP)
                case InstanceCommands.STEP:
                    instance.state_controller.command_queue.put(InstanceCommands.STEP)
        
        except ValueError:
            pass


    @staticmethod
    def _route_state_setters(msg_type: ClientMessages, payload: dict, instance: ServerInstance):
        match msg_type:
            case ClientMessages.SET_INSTANCE_STATE:
                try:
                    new_state = InstanceStates(payload.get("state", -1))
                    instance.state_controller.queue_state(new_state)
                except ValueError:
                    pass

            case ClientMessages.SET_INSTANCE_LOOP_STATE:
                try:
                    new_state = LoopStates(payload.get("state", -1))
                    instance.state_controller.queue_loop_state(new_state)
                except ValueError:
                    pass
    
    
    def _route_scene_commands(self, msg_type: ClientMessages, payload: dict, instance: ServerInstance):
        match msg_type:
            case ClientMessages.LOAD_SCENE:
                # FIXME is the payload supposed to be the full scene?
                instance.load_new_scene(payload)
                return
            
            case ClientMessages.SYNC_CLIENT_SCENE:
                return {"type": ServerMessages.SYNC_CLIENT_SCENE.value, "payload": instance._scene.mirror_manager.scene_reader.raw_data}
        
        uid = payload.get("uid", None)
        action = payload.get("action", None)
        if not uid or not action:
            return
        
        try:
            action_type = SceneActions(str(action).upper())
            match msg_type:
                case ClientMessages.NODE_ACTION:
                    self._parse_node_commands(uid, action_type, payload, instance)
                    return

                case ClientMessages.CONNECTION_ACTION:
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