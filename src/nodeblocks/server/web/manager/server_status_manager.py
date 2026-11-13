
from typing import Optional

from nodeblocks.server.protocols.web.messages.server.server_events import ServerStatusEvent, ServerStatuses
from nodeblocks.server.web.manager.server_session_manager import ServerSessionManager


class ServerStatusManager:
    session_manager: ServerSessionManager
    status: ServerStatuses

    def __init__(self, session_manager: ServerSessionManager) -> None:
        self.session_manager = session_manager
        self.status = ServerStatuses.INITIALIZING

    async def update_server_status(self, status: ServerStatuses, message: Optional[str] = None):
        self.status = status
        await self.session_manager.broadcast(ServerStatusEvent(
            status=status,
            message=message
        ))

    async def send_current_status(self, session_id: str):
        message = self.session_manager.encode_event(ServerStatusEvent(
            status=self.status,
        ))
        await self.session_manager.send_to_connection_id(message, session_id)

    # TODO: talvez fazer uma queue de status update e sempre enviar o último status
    # assim a gente faz um método síncrono que adiciona à queue e uma task
    # envia o status fazendo broadcast
