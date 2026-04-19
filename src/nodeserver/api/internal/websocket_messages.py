from typing import Optional
from nodeserver.api.web.requests.client_requests import ClientCommand, ClientCommandAdapter
from nodeserver.api.web.requests.websocket_requests import ServerMessage

class SocketMessage[MessageType: ServerMessage | ClientCommand]:
    msg: MessageType
    raw_message: dict

    def __init__(self, raw_message: dict, message_data: MessageType) -> None:
        self.raw_message = raw_message
        self.msg = message_data


    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.msg.type})"
        # return f"{self.__class__.__name__}({self.message.type.value}, payload_keys={list(self.message.payload.keys() if self.payload else [])})"

# class ServerMessage(SocketMessage[ServerMessages]): 
#     def __init__(self, raw_message: dict, message_data: Annotated) -> None:
#         super().__init__(raw_message, message_data)

class ClientMessage(SocketMessage[ClientCommand]):
    def __init__(self, raw_message: dict, message_data: ClientCommand) -> None:
        super().__init__(raw_message, message_data)


class MessageUtils:
    @staticmethod
    def parse_client_message(message_dict: dict) -> Optional[ClientMessage]:
        try:
            command = ClientCommandAdapter.validate_python(message_dict)
            return ClientMessage(message_dict, command) 
        
        except Exception as e:
            print(f"Invalid Message Structure: {e}")
            return None