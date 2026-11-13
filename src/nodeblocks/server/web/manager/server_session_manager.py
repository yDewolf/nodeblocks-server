
import logging

from nodeblocks.server.protocols.session.server_connection import ServerConnectionSession
from nodeblocks.server.protocols.web.messages.server.server_events import BaseServerEvent

logger = logging.getLogger("nds.server")

# TODO: create a server status controller
# TODO: send current server status to new connections
class ServerSessionManager:
    _connections: dict[str, ServerConnectionSession]

    def __init__(self) -> None:
        self._connections = {}

    def register_connection(self, session: ServerConnectionSession):
        self._connections[session.id] = session
        logger.info("New server connection: %s", session.id)

    def unregister_connection(self, id: str):
        session = self._connections.pop(id, None)
        if session:
            logger.info("Closed connection '%s", id)


    async def broadcast(self, event: BaseServerEvent):
        encoded_message = self.encode_event(event)
        for session_id, session in list(self._connections.items()):
            await self.send_to_connection(encoded_message, session)

    async def send_to_connection(self, encoded_message: bytes, connection: ServerConnectionSession):
        try:
            await connection.socket.write(encoded_message)
        
        except Exception as e:
            logger.error("Failed to send event to connection %s: %s", connection.id, e)
            self.unregister_connection(connection.id)


    def encode_event(self, event: BaseServerEvent) -> bytes:
        payload = event.model_dump_json()
        message_parts: list[str] = []
        
        message_parts.append(f"event: {event.type}")
        message_parts.append(f"data: {payload}\n\n")
        
        encoded_message = "\n".join(message_parts).encode("utf-8")
        return encoded_message
