from enum import Enum

class WebsocketStatus(Enum):
    ERROR = -1
    CONNECTED = 1
    DISCONNECTED = 0

class ServerMessages(Enum):
    HANDSHAKE_SYNC = "handshake_sync"
    NODE_OUTPUT = "node_output"
    SYNC_CLIENT_SCENE = "sync_client_scene"
    SYNC_INSTANCE_STATE = "sync_instance_state"
    SYNC_ACTION = "sync_action"

class ClientMessages(Enum):
    LOAD_SCENE = "LOAD_SCENE"
    SYNC_CLIENT_SCENE = "SYNC_CLIENT_SCENE"
    GET_TYPES = "GET_TYPES"
    
    SET_INSTANCE_STATE = "SET_STATE"
    SET_INSTANCE_LOOP_STATE = "SET_LOOP_STATE"

    NODE_ACTION = "NODE"
    CONNECTION_ACTION = "CONNECTION"

    INSTANCE_COMMAND = "INSTANCE"

class SceneActions(Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"
    UPDATE = "UPDATE"

class EditorActionStatus(Enum):
    SUCCESSFULL = "SUCCESSFULL",
    UNSYNCED = "UNSYNCED",
    FAILED = "FAILED"
    