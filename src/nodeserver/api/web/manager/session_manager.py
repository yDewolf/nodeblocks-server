import datetime
import logging
import os

from nodeserver.api.utils.env_variables import SESSION_GRACE_PERIOD
from nodeserver.api.utils.session_utils import UserSession, create_session_token, validate_session_token

logger = logging.getLogger("nds.websocket")

class SessionManager:
    # Token -> Session
    grace_period_seconds: int = 120
    sessions: dict[str, UserSession]

    def __init__(self) -> None:
        self.grace_period_seconds = SESSION_GRACE_PERIOD
        
        self.sessions = {}

    def start_session(self, user_id: str, instance_id: str) -> UserSession:
        session = SessionManager.create_session(user_id, instance_id)
        
        self.sessions[session.token] = session
        return session

    def finish_session(self, token: str) -> UserSession:
        session = self.sessions.pop(token)
        return session


    def _clean_inactive_sessions(self) -> list[UserSession]:
        removed_sessions: list[UserSession] = []
        now = datetime.datetime.now(datetime.timezone.utc)
        for token, session in self.sessions.items():
            if not session.is_disconnected: continue
            payload = validate_session_token(token)
            
            time_passed = (now - session.disconnected_at).total_seconds()
            is_zombie = session.is_disconnected and time_passed > self.grace_period_seconds
            
            if payload is None or is_zombie:
                try: 
                    removed_sessions.append(session)

                except KeyError:
                    logger.warning(f"Tried to remove a session that wasn't indexed - Token: {token}")

        for session in removed_sessions:
            self.finish_session(session.token)

        return removed_sessions

    def get_session(self, token: str) -> UserSession | None:
        return self.sessions.get(token)

    def get_session_by_instance(self, instance_id: str) -> UserSession | None:
        for session in self.sessions.values():
            if session.instance_id == instance_id:
                return session
        return None

    @staticmethod
    def create_session(user_id: str, instance_id: str) -> UserSession:
        return UserSession(
            create_session_token(
                user_id, 
                instance_id
            ), instance_id
        )