from abc import ABC

import logging
from pydantic import ValidationError

from nodeserver.server.protocols.providers.scene_worker_manager_protocol import ISceneWorkerManager
from nodeserver.server.protocols.session_protocols import SceneConnectionSession
from nodeserver.server.web.handlers.base_command_handler import BaseSceneCmdHandler

logger = logging.getLogger("nds.server")

class WSSceneMessageDispatcher(ABC):
    _handlers: dict[str, BaseSceneCmdHandler]
    def __init__(self, handlers: dict[str, BaseSceneCmdHandler]) -> None:
        self._handlers = handlers

    async def dispatch(
        self,
        raw_json: dict,
        session: SceneConnectionSession,
        worker_manager: ISceneWorkerManager
    ):
        try:
            wrapper = ClientMessageWrapper(payload=raw_json)
            parsed_message = wrapper.payload
        
        except ValidationError as e:
            logger.warning(f"Mensagem WebSocket inválida de {session.user.user_id}: {e}")
            await session.socket.send_json({"error": "validation_error", "details": e.errors()})
            return

        # 2. Localiza o handler correspondente
        handler = self._handlers.get(parsed_message.cmd_group)
        if not handler:
            logger.error(f"Nenhum handler registrado para o grupo: {parsed_message.cmd_group}")
            return

        # 3. Gatekeeper: Valida se a sessão tem a permissão necessária
        if not session.has_permission(handler.required_permission):
            logger.warning(f"User {session.user.user_id} blocked. Requer {handler.required_permission}")
            await session.socket.send_json({
                "error": "permission_denied", 
                "message": f"Requires {handler.required_permission.name} permission."
            })
            return

        # 4. Executa o handler
        await handler.handle(parsed_message, session, worker_manager)
