from aiohttp import web
import os

# Very WIP (made by gemini lol)
class FileHandler:
    async def list_files(self, request):
        user_id = request.match_info['user_id']
        upload_path = os.path.join("workspaces", user_id, "uploads")
        
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

    async def delete_file(self, request):
        user_id = request.match_info['user_id']
        filename = request.match_info['filename']

        safe_name = os.path.basename(filename)
        file_path = os.path.join("workspaces", user_id, "uploads", safe_name)

        if os.path.exists(file_path):
            os.remove(file_path)
            return web.json_response({"status": "deleted"})
        return web.Response(status=404)

    async def download_file(self, request):
        user_id = request.match_info['user_id']
        filename = request.match_info['filename']
        file_path = os.path.join("workspaces", user_id, "uploads", os.path.basename(filename))
        
        return web.FileResponse(file_path)
