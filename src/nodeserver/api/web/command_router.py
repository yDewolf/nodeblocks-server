from enum import Enum
import json
import logging

from nodeserver.api.actions.action_controller import Action
from nodeserver.api.base_nodes import BaseNode
from nodeserver.api.instance_states import InstanceCommands, InstanceStates, LoopStates
from nodeserver.api.internal.websocket_messages import ClientMessage
from nodeserver.api.internal.websocket_protocol import ClientMessages, SceneActions, ServerMessages
from nodeserver.api.server_instance import ServerInstance
from nodeserver.networking.nodes.helpers.file.node_scene_dataclasses import ConnectionSceneData, NodeSceneData

COMMAND_LOGGER = logging.getLogger("nds.commands")
# FIXME: Make requests Type Safe
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

        
        raw_action_type = message.payload.get("action", None)
        if not raw_action_type:
            return
        
        try:
            raw_action_type = SceneActions(str(raw_action_type).upper())
            match message.type:
                case ClientMessages.NODE_ACTION:
                    node_action: Action = Action(message.raw_message.get("action_uid", ""), message, raw_action_type, message.type)
                    instance.action_controller.queue_action(node_action)
                    # return self._parse_node_commands(uids, raw_action_type, action_data, instance)

                case ClientMessages.CONNECTION_ACTION:
                    conn_action: Action = Action(message.raw_message.get("action_uid", ""), message, raw_action_type, message.type)
                    instance.action_controller.queue_action(conn_action)
                    # return self._parse_conn_commands(uids, raw_action_type, action_data, instance)
        
        except ValueError:
            # TODO: Handle Error
            pass
