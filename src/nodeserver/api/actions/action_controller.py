
from queue import Queue
from typing import Literal

from nodeserver.api.internal.websocket_messages import ClientMessageWrapper
from nodeserver.api.web.websocket_protocol import ClientMessages, EditorActionStatus, SceneActionTypes

class Action:
    uid: str
    type: SceneActionTypes
    target_type: Literal[ClientMessages.NODE_ACTION] | Literal[ClientMessages.CONNECTION_ACTION]

    message: ClientMessageWrapper

    def __init__(self, uid: str, message: ClientMessageWrapper, type: SceneActionTypes, target_type: Literal[ClientMessages.NODE_ACTION] | Literal[ClientMessages.CONNECTION_ACTION]) -> None:
        self.uid = uid
        self.message = message
        self.type = type
        self.target_type = target_type

class ActionController:

    action_queue: Queue[Action]
    # Actions that already got synced and needs to be sent to client
    synced_actions: Queue[Action]

    def __init__(self) -> None:
        self.action_queue = Queue()


    def queue_action(self, action: Action):
        self.action_queue.put(action, False)
    

    def parse_actions(self) -> dict[str, EditorActionStatus]:
        action_statuses: dict[str, EditorActionStatus] = {}
        
        return action_statuses
