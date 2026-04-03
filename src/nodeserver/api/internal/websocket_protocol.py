from enum import Enum

class WebsocketStatus(Enum):
    ERROR = -1
    CONNECTED = 1
    DISCONNECTED = 0

class ServerMessages(Enum):
    HANDSHAKE_SYNC = "handshake_sync"
    SYNC_CLIENT_SCENE = "sync_client_scene"