from abc import ABC

import logging
from pydantic import ValidationError

from nodeserver.server.protocols.providers.scene_worker_manager_protocol import ISceneWorkerManager
from nodeserver.server.protocols.session_protocols import SceneConnectionSession
from nodeserver.server.protocols.web.messages.base_client_command import CommandGroups
from nodeserver.server.protocols.web.messages.client_message_wrapper import ClientCommandAdapter, ClientCommandPayloadAdapter, ClientMessageWrapper
from nodeserver.server.web.handlers.base_command_handler import BaseSceneCmdHandler

logger = logging.getLogger("nds.server")

class WSSceneCommandDispatcher(ABC):
    _handlers: dict[CommandGroups, BaseSceneCmdHandler]
    def __init__(self, handlers: dict[CommandGroups, BaseSceneCmdHandler]) -> None:
        self._handlers = handlers

    async def dispatch(
        self,
        raw_payload: dict,
        session: SceneConnectionSession,
        worker_manager: ISceneWorkerManager
    ):
        try:
            parsed_message = ClientCommandPayloadAdapter.validate_python(raw_payload)
        
        except ValidationError as e:
            logger.warning(f"Invalid websocket message from {session.user.user_id}: {e}")
            await session.socket.send_json({"error": "validation_error", "details": e.errors()})
            return

        handler = self._handlers.get(parsed_message.cmd_group)
        if not handler:
            logger.error(f"No handler was registered for group: {parsed_message.cmd_group}")
            return

        if not session.has_permission(handler.required_permission):
            logger.warning(f"User {session.user.user_id} isn't allowed to use command: {parsed_message.__class__.__name__}. Must have {handler.required_permission}")
            await session.socket.send_json({
                "error": "permission_denied", 
                "message": f"Requires {handler.required_permission.name} permission."
            })
            return

        await handler.handle(parsed_message, session, worker_manager)
