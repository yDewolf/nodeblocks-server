import json

from nodeserver.api.internal.websocket_protocol import ClientMessages, ServerMessages

class SocketMessage[MessageType: ServerMessages | ClientMessages]:
    type: MessageType
    payload: dict | None
    raw_message: dict

    def __init__(self, raw_message: dict, message_type: MessageType, payload: dict | None = None) -> None:
        self.raw_message = raw_message
        self.type = message_type
        self.payload = payload

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "payload": self.payload
        }

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.type.value}, payload_keys={list(self.payload.keys() if self.payload else [])})"

class ServerMessage(SocketMessage[ServerMessages]): 
    def __init__(self, raw_message: dict, message_type: ServerMessages, payload: dict | None = None) -> None:
        super().__init__(raw_message, message_type, payload)

class ClientMessage(SocketMessage[ClientMessages]):
    def __init__(self, raw_message: dict, message_type: ClientMessages, payload: dict | None = None) -> None:
        super().__init__(raw_message, message_type, payload)


class MessageUtils:
    @staticmethod
    def client_from_dict(message_dict: dict) -> ClientMessage | None:
        try:
            message_type = ClientMessages(message_dict.get("type", ""))
        except ValueError:
            return None

        payload = message_dict.get("payload", "{}")
        if type(payload) is str:
            payload = json.loads(payload)
        
        if not type(payload) is dict:
            return None
        
        return ClientMessage(message_dict, message_type, payload)