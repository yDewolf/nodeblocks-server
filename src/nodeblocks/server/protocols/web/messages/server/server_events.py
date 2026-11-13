
from enum import StrEnum
from typing import Annotated, Literal, Optional

from pydantic import Field

from nodeblocks.server.protocols.web.base_socket_model import BaseSocketModel


class ServerEventTypes(StrEnum):
    SERVER_STATUS = "server_status"

class BaseServerEvent(BaseSocketModel):
    type: ServerEventTypes = Field(exclude=True)


# TODO: implementar isso aqui no formato de tasks que tem início e fim
class ServerStatuses(StrEnum):
    INITIALIZING = "initializing"
    SETTING_UP = "setting_up"
    READY = "ready"
    FAILED = "failed"

class ServerStatusEvent(BaseServerEvent):
    type: Literal[ServerEventTypes.SERVER_STATUS] = ServerEventTypes.SERVER_STATUS
    status: ServerStatuses
    message: Optional[str] = Field(default=None)
