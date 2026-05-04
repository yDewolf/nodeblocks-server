from typing import Annotated, Union

from pydantic import Field, TypeAdapter

from nodeserver.api.web.requests.client_requests import BaseClientCommands
from nodeserver.api.web.requests.notification_requests import ClientNotificationMessages, ServerNotification, ServerNotificationMessages
from nodeserver.api.web.requests.websocket_requests import BaseServerMessages


AnyClientMessage = Annotated[
    Union[
        BaseClientCommands, ClientNotificationMessages
    ],
    Field(discriminator="type")
]
ClientMessageAdapter = TypeAdapter(AnyClientMessage)

AnyServerMessage = Annotated[
    Union[
        BaseServerMessages, ServerNotificationMessages
    ],
    Field(discriminator="type")
]
ServerMessageAdapter = TypeAdapter(AnyServerMessage)