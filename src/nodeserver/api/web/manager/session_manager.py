import datetime
import logging
import os
from typing import Optional

from nodeserver.api.utils.env_variables import SESSION_GRACE_PERIOD
from nodeserver.api.web.session.user_session import SessionUtils, UserSession

logger = logging.getLogger("nds.websocket")

class SessionManager:
    # Token -> Session
    grace_period_seconds: int = 120
    sessions: dict[str, UserSession]

    def __init__(self) -> None:
        self.grace_period_seconds = SESSION_GRACE_PERIOD
        
        self.sessions = {}

    def start_session(self, session: UserSession, instance_id: str) -> UserSession:
        session_token = SessionUtils.create_session_token(session.user_id, instance_id)
        session.token = session_token

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
            payload = SessionUtils.validate_session_token(token)
            
            time_passed = (now - session.disconnected_at).total_seconds()
            is_zombie = session.is_disconnected and time_passed > self.grace_period_seconds
            
            if payload is None or is_zombie:
                try: 
                    removed_sessions.append(session)

                except KeyError:
                    logger.warning(f"Tried to remove a session that wasn't indexed - Token: {token}")

        for session in removed_sessions:
            if not session.token:
                continue
            
            self.finish_session(session.token)

        return removed_sessions

    def get_session(self, token: str) -> UserSession | None:
        return self.sessions.get(token)

    def get_session_by_instance(self, instance_id: str) -> UserSession | None:
        for session in self.sessions.values():
            if session.workspace.instance_id == instance_id:
                return session
        return None

    @staticmethod
    def create_session(user_id: str, instance_id: Optional[str]) -> UserSession:
        session_token: Optional[str] = None
        if instance_id:
            session_token = SessionUtils.create_session_token(user_id, instance_id)
        
        return UserSession(
            session_token, user_id
        )