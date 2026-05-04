import json
from typing import Optional

from nodeserver.api.web.requests.request_unions import AnyClientMessage, AnyServerMessage, ClientMessageAdapter

class SocketMessage[MessageType: AnyServerMessage | AnyClientMessage]:
    msg: MessageType
    raw_message: dict

    def __init__(self, raw_message: dict, message_data: MessageType) -> None:
        self.raw_message = raw_message
        self.msg = message_data


    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.msg.type})"
        # return f"{self.__class__.__name__}({self.message.type.value}, payload_keys={list(self.message.payload.keys() if self.payload else [])})"

class ServerMessageWrapper(SocketMessage[AnyServerMessage]): 
    def __init__(self, raw_message: dict, message_data: AnyServerMessage) -> None:
        super().__init__(raw_message, message_data)

class ClientMessageWrapper(SocketMessage[AnyClientMessage]):
    def __init__(self, raw_message: dict, message_data: AnyClientMessage) -> None:
        super().__init__(raw_message, message_data)


class MessageUtils:
    @staticmethod
    def parse_client_message(message_str: str) -> Optional[ClientMessageWrapper]:
        try:
            command = ClientMessageAdapter.validate_json(message_str)
            message_dict = json.loads(message_str)
            return ClientMessageWrapper(message_dict, command) 
        
        except Exception as e:
            print(f"Invalid Message Structure: {e}")
            return None