from enum import Enum

class WebsocketStatus(Enum):
    ERROR = -1
    CONNECTED = 1
    DISCONNECTED = 0

class WebsocketCommands(Enum):
    pass