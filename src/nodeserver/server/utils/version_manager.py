import hashlib
import os

class VersionManager:
    MAJOR = "1"

    @staticmethod
    def get_protocol_hash():
        protocol_files = ["node_definitions.py", "server.py"]
        hasher = hashlib.md5()
        
        for file in protocol_files:
            if os.path.exists(file):
                with open(file, "rb") as f:
                    hasher.update(f.read())
        
        return hasher.hexdigest()[:8]

    @classmethod
    def get_full_version(cls):
        return f"{cls.MAJOR}.{cls.get_protocol_hash()}"