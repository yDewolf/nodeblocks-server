from enum import Enum
import json
import logging

from nodeserver.api.instance_states import InstanceCommands, InstanceStates, LoopStates
from nodeserver.api.internal.websocket_messages import ClientMessage
from nodeserver.api.internal.websocket_protocol import ClientMessages, SceneActions, ServerMessages
from nodeserver.api.server_instance import ServerInstance
from nodeserver.networking.nodes.helpers.file.node_scene_dataclasses import ConnectionSceneData, NodeSceneData

COMMAND_LOGGER = logging.getLogger("nds.commands")

class BaseCommandRouter:
    def route_message(self, message: ClientMessage, instance: ServerInstance) -> dict | None:
        # TODO: Simplify this if return mess
        COMMAND_LOGGER.info(f"Routing command for instance {instance._attributed_id} Message: {message}")
        try:
            out = self._route_utility_commands(message, instance)
            if out != None: return out
            
            out = self._route_state_setters(message, instance)
            if out != None: return out
            
            out = self._route_state_commands(message, instance)
            if out != None: return out

            out = self._route_scene_commands(message, instance)
            if out != None: return out
        
        except ValueError as e:
            pass


    @staticmethod
    def _route_utility_commands(message: ClientMessage, instance: ServerInstance) -> dict |  None:
        match message.type:
            case ClientMessages.GET_TYPES:
                return {"type": message.type, "payload": json.dumps(instance.mirror_manager.type_reader.serialize_to_dict())}

    @staticmethod
    def _route_state_commands(message: ClientMessage, instance: ServerInstance):
        if message.type != ClientMessages.INSTANCE_COMMAND:
            return
        
        if not message.payload:
            return

        try:
            command = InstanceCommands(message.payload.get("action", "").upper())
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
    def _route_state_setters(message: ClientMessage, instance: ServerInstance):
        if not message.payload:
            return
        
        match message.type:
            case ClientMessages.SET_INSTANCE_STATE:
                try:
                    new_state = InstanceStates(message.payload.get("state", -1))
                    instance.state_controller.queue_state(new_state)
                except ValueError:
                    pass

            case ClientMessages.SET_INSTANCE_LOOP_STATE:
                try:
                    new_state = LoopStates(message.payload.get("state", -1))
                    instance.state_controller.queue_loop_state(new_state)
                except ValueError:
                    pass
    
    
    # TODO: Create Action Stack to fill when instance is running
    def _route_scene_commands(self, message: ClientMessage, instance: ServerInstance):
        match message.type:
            case ClientMessages.LOAD_SCENE:
                if not message.payload:
                    return
                # FIXME is the payload supposed to be the full scene?
                instance.load_new_scene(message.payload)
                return
            
            case ClientMessages.SYNC_CLIENT_SCENE:
                scene_data = instance._scene.mirror_manager.get_scene_as_dict()
                return {
                    "type": ServerMessages.SYNC_CLIENT_SCENE.value, 
                    "payload": scene_data
                }
        
        if not message.payload:
            return
    
        uid = message.payload.get("uid", None)
        action = message.payload.get("action", None)
        if not uid or not action:
            return
        
        try:
            action_type = SceneActions(str(action).upper())
            action_data = message.payload.get("action_data", {})
            match message.type:
                case ClientMessages.NODE_ACTION:
                    self._parse_node_commands(uid, action_type, action_data, instance)
                    return

                case ClientMessages.CONNECTION_ACTION:
                    self._parse_conn_commands(uid, action_type, action_data, instance)
                    return
        
        except ValueError:
            # TODO: Handle Error
            pass

    @staticmethod
    def _parse_node_commands(node_uid: str, action: SceneActions, action_data: dict, instance: ServerInstance):
        match action:
            case SceneActions.ADD:
                node_data = NodeSceneData.from_dict(action_data, node_uid)
                mirror = instance.mirror_manager.add_node_mirror(node_data, node_data.uid)
                if not mirror:
                    return
                
                node = instance._scene.build_node(mirror)
                if node:
                    instance._scene.add_node(node)
                    instance._scene.update_nodes()

            case SceneActions.REMOVE:
                instance.mirror_manager.remove_node_mirror(node_uid)
                instance._scene.update_nodes()


    @staticmethod
    def _parse_conn_commands(conn_uid: str, action: SceneActions, action_data: dict, instance: ServerInstance):
        match action:
            case SceneActions.ADD:
                conn_data = ConnectionSceneData.from_dict(action_data, conn_uid)
                connection = instance.mirror_manager.add_conn_mirror(conn_data)
                instance._scene.update_nodes()

            case SceneActions.REMOVE:
                instance.mirror_manager.remove_conn_mirror(conn_uid)
                instance._scene.update_nodes()