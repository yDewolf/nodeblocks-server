from abc import abstractmethod
from enum import Enum
from typing import Optional
from aiohttp import web
import aiohttp_cors
from nodeserver.api.web.manager.session_manager import SessionManager
from nodeserver.api.web.session.user_session import UserSession

class BaseRequestRouter:
    session_manager: SessionManager
    def __init__(self, session_manager: SessionManager) -> None:
        self.session_manager = session_manager

    @abstractmethod
    async def route_request(self, request: web.Request, request_type: Enum, cors: aiohttp_cors.CorsConfig) -> web.StreamResponse:
        pass
    
    @abstractmethod
    def setup_http_routes(self, app: web.Application, host: str):
        pass


class RestUtils:
    @staticmethod
    def get_session_from_request(session_manager: SessionManager, request: web.Request) -> tuple[Optional[UserSession], Optional[web.Response]]:
        token = request.query.get("token")
        if not token:
            return (None, web.json_response({"message": "Missing session token"}))
        
        user_session = session_manager.get_session(token)
        if not user_session:
            return (None, web.json_response({"message": "Session is not loaded"}))

        return (user_session, None)