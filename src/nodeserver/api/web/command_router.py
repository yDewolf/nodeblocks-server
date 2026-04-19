from enum import Enum
import json
import logging

from nodeserver.api.actions.action_controller import Action
from nodeserver.api.internal.websocket_messages import ClientMessageWrapper
from nodeserver.api.web.requests.client_requests import ClientCommand, MsgConnectionAction, MsgInstanceCommand, MsgInstanceState, MsgLoadScene, MsgLoopState, MsgNodeAction, MsgSimple
from nodeserver.api.web.websocket_protocol import ClientMessages, ServerMessages
from nodeserver.api.server_instance import ServerInstance
from nodeserver.networking.nodes.helpers.file.node_scene_dataclasses import ConnectionSceneData, NodeSceneData

COMMAND_LOGGER = logging.getLogger("nds.commands")
class CommandRouter:
    def route_message(self, message: ClientMessageWrapper, instance: ServerInstance) -> dict | None:
        COMMAND_LOGGER.info(f"Routing command: {message.msg.type}")

        if isinstance(message.msg, MsgSimple):
            if message.msg.type == ClientMessages.SYNC_CLIENT_SCENE:
                return {
                    "type": ServerMessages.SYNC_CLIENT_SCENE.value,
                    "payload": instance._scene.mirror_manager.get_scene_as_dict()
                }

        elif isinstance(message.msg, MsgInstanceState):
            instance.state_controller.queue_state(message.msg.payload.state)

        elif isinstance(message.msg, MsgLoopState):
            instance.state_controller.queue_loop_state(message.msg.payload.state)
        
        elif isinstance(message.msg, MsgInstanceCommand):
            instance.state_controller.queue_command(message.msg.payload.action)

        elif isinstance(message.msg, MsgNodeAction):
            action = Action(
                uid=message.msg.action_uid,
                message=message,
                type=message.msg.payload.action,
                target_type=message.msg.type
            )
            instance.action_controller.queue_action(action)

        elif isinstance(message.msg, MsgConnectionAction):
            action = Action(
                uid=message.msg.action_uid,
                message=message,
                type=message.msg.payload.action,
                target_type=message.msg.type
            )
            instance.action_controller.queue_action(action)

        elif isinstance(message.msg, MsgLoadScene):
            instance.load_new_scene(message.msg.payload)

        return None