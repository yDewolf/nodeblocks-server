from enum import Enum
from typing import Optional

from aiohttp import web
import os

from nodeserver.api.web.manager.session_manager import SessionManager
from nodeserver.api.web.requests.websocket_requests import SrvSyncFiles
from nodeserver.api.web.session.user_session import UserSession

class FileRequestType(Enum):
    GET = 0
    DELETE = 1
    UPLOAD = 2
    DOWNLOAD = 3

class FileHandler:
    session_manager: SessionManager

    def __init__(self, session_manager: SessionManager) -> None:
        self.session_manager = session_manager

    async def route_file_request(self, request: web.Request, request_type: FileRequestType) -> web.StreamResponse:
        user_session, error = self.get_session_from_request(request)
        if error: return error
        if not user_session: return web.json_response({})

        result = web.json_response({"message": "internal_error"}, status=400)
        match request_type:
            case FileRequestType.GET: result = self._list_files(request, user_session) 
            case FileRequestType.DELETE: result = self._delete_file(request, user_session)
            case FileRequestType.DOWNLOAD: result = self._download_file(request, user_session)
            case FileRequestType.UPLOAD: return await self._upload_file(request, user_session)
        
        if request_type != FileRequestType.GET:
            user_session.workspace.send_msg_as_instance(SrvSyncFiles())
        
        return result

    async def list_files(self, request: web.Request):
        return await self.route_file_request(request, FileRequestType.GET)
    
    async def delete_file(self, request: web.Request):
        return await self.route_file_request(request, FileRequestType.DELETE)
    
    async def download_file(self, request: web.Request):
        return await self.route_file_request(request, FileRequestType.DOWNLOAD)
    
    async def upload_file(self, request: web.Request):
        return await self.route_file_request(request, FileRequestType.UPLOAD)


    def _list_files(self, request: web.Request, user_session: UserSession):
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

    def _delete_file(self, request: web.Request, user_session: UserSession):
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

    def _download_file(self, request: web.Request, user_session: UserSession):
        filename = request.query.get("filename")
        if not filename:
            return web.json_response({"message": "missing filename"})
        upload_path = user_session.workspace.get_uploads_path()
        file_path = os.path.join(upload_path, os.path.basename(filename))
        
        return web.FileResponse(file_path)

    async def _upload_file(self, request: web.Request, user_session: UserSession):
        upload_path = user_session.workspace.get_uploads_path()
        reader = await request.multipart()

        field = await reader.next()
        if field.name == "file": # type: ignore
            filename = os.path.basename(field.filename) # type: ignore
            file_path = os.path.join(upload_path, filename)

            with open(file_path, "wb") as f:
                while True:
                    chunk = await field.read_chunk() # type: ignore
                    if not chunk:
                        break
                    f.write(chunk)

        user_session.workspace.send_msg_as_instance(SrvSyncFiles())
        return web.json_response({"message": "Uploaded File Successfully", "filename": filename})

    
    def get_session_from_request(self, request: web.Request) -> tuple[Optional[UserSession], Optional[web.Response]]:
        token = request.query.get("token")
        if not token:
            return (None, web.json_response({"message": "Missing session token"}))
        
        user_session = self.session_manager.get_session(token)
        if not user_session:
            return (None, web.json_response({"message": "Session is not loaded"}))

        return (user_session, None)