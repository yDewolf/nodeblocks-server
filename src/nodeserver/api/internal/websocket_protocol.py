from enum import Enum

class WebsocketStatus(Enum):
    ERROR = -1
    CONNECTED = 1
    DISCONNECTED = 0

class ServerMessages(Enum):
    HANDSHAKE_SYNC = "handshake_sync"