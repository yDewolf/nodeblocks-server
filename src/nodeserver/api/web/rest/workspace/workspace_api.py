from typing import Optional

from aiohttp import web
import os

from nodeserver.api.web.manager.session_manager import SessionManager
from nodeserver.api.web.session.user_session import UserSession

class FileHandler:
    session_manager: SessionManager

    def __init__(self, session_manager: SessionManager) -> None:
        self.session_manager = session_manager

    async def list_files(self, request: web.Request):
        user_session, error = self.get_session_from_request(request)
        if error: return error
        if not user_session: return web.json_response({})

        upload_path = user_session.workspace.get_uploads_path()
        if not os.path.exists(upload_path):
            return web.json_response([])

        files = []
        for filename in os.listdir(upload_path):
            path = os.path.join(upload_path, filename)
            files.append({
                "name": filename,
                "size": os.path.getsize(path),
                "type": "file" if os.path.isfile(path) else "folder"
            })
        
        return web.json_response(files)

    async def delete_file(self, request: web.Request):
        user_session, error = self.get_session_from_request(request)
        if error: return error
        if not user_session: return web.json_response({})
        
        filename = request.query.get("filename")
        if not filename:
            return web.json_response({"message": "missing filename"})

        safe_name = os.path.basename(filename)
        upload_path = user_session.workspace.get_uploads_path()
        file_path = os.path.join(upload_path, safe_name)

        if os.path.exists(file_path):
            os.remove(file_path)
            return web.json_response({"status": "deleted"})

        return web.json_response({"message": "File doesn't exist"}, status=404)

    async def download_file(self, request: web.Request):
        user_session, error = self.get_session_from_request(request)
        if error: return error
        if not user_session: return web.json_response({})
        
        filename = request.query.get("filename")
        if not filename:
            return web.json_response({"message": "missing filename"})
        upload_path = user_session.workspace.get_uploads_path()
        file_path = os.path.join(upload_path, os.path.basename(filename))
        
        return web.FileResponse(file_path)

    
    def get_session_from_request(self, request: web.Request) -> tuple[Optional[UserSession], Optional[web.Response]]:
        token = request.query.get("token")
        if not token:
            return (None, web.json_response({"message": "Missing session token"}))
        
        user_session = self.session_manager.get_session(token)
        if not user_session:
            return (None, web.json_response({"message": "Session is not loaded"}))

        return (user_session, None)