
import datetime
import logging
from typing import Optional

from nodeserver.server.protocols.session_protocols import SceneConnectionSession

logger = logging.getLogger("nds.server")

class SceneSessionManager:
    _scenes: dict[str, dict[str, SceneConnectionSession]] # scene_id -> {token -> session}
    _connections: dict[str, SceneConnectionSession] # token -> session

    def __init__(self) -> None:
        self._scenes = {}
        self._connections = {}


    def register_connection(self, session: SceneConnectionSession):
        if not session.scene_id in self._scenes:
            raise Exception("Tried to connect to a not initialized scene") # TODO: better exception
        
        self._scenes[session.scene_id][session.id] = session
        self._connections[session.id] = session
        logger.info(
            f"User '{session.user.user_id}' connected to scene '{session.scene_id}' [Conn: {session.id}]"
        )

    def unregister_connection(self, connection_id: str):
        session = self._connections.pop(connection_id, None)
        if session:
            self._scenes[session.scene_id].pop(connection_id, None)
            if not self._scenes[session.scene_id]:
                del self._scenes[session.scene_id]
            
            logger.info(
                f"Closed connection '{connection_id}' for scene '{session.scene_id}'"
            )

    def get_scene_sessions(self, scene_id: str) -> list[SceneConnectionSession]:
        return list(self._scenes.get(scene_id, {}).values())

    async def broadcast_to_scene(
        self,
        scene_id: str,
        message: dict,
        exclude_conn_id: Optional[str] = None,
    ):
        sessions = self.get_scene_sessions(scene_id)
        for session in sessions:
            if exclude_conn_id and session.id == exclude_conn_id:
                continue
            try:
                await session.socket.send_json(message)
            
            except Exception as e:
                logger.error(
                    f"Failed to send message to connection {session.id}: {e}"
                )
