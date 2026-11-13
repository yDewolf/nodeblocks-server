
import logging

from nodeblocks.server.protocols.session.server_connection import ServerConnectionSession

logger = logging.getLogger("nds.server")

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
