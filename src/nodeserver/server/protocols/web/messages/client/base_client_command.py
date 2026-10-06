from enum import StrEnum
from nodeserver.server.protocols.web.base_socket_model import BaseSocketModel

class CommandGroups(StrEnum):
    SCENE = "scene"
    GRAPH = "graph"
    NOTIFICATION = "notification"
    EXECUTION = "execution"


class BaseClientCommand(BaseSocketModel):
    cmd_uid: str # used for command responses
    cmd_group: CommandGroups

