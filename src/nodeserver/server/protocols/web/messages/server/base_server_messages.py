from enum import StrEnum
from typing import Any, Literal

from nodeserver.engine.runtime.protocols.engine_events import IPCEngineEvent
from nodeserver.engine.workers.scene.protocols.scene_worker_protocol import IPCSceneWorkerEvent
from nodeserver.server.protocols.web.base_socket_model import BaseSocketModel

class ServerMessageTypes(StrEnum):
    SCENE_EVENT = "scene_event"
    COMMAND_RESPONSE = "cmd_response"

class BaseServerMessage(BaseSocketModel):
    type: ServerMessageTypes


class ServerEngineEventWrapper(BaseServerMessage):
    type: Literal[ServerMessageTypes.SCENE_EVENT] = ServerMessageTypes.SCENE_EVENT
    event_type: str
    data: IPCEngineEvent


# TODO: move these to other files
class BaseServerCmdResponse(BaseServerMessage):
    type: Literal[ServerMessageTypes.COMMAND_RESPONSE] = ServerMessageTypes.COMMAND_RESPONSE
    cmd_uid: str
    response_payload: Any # TODO: create models for this
