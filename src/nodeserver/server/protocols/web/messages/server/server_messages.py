from enum import StrEnum
from typing import Any, Literal, Optional

from nodeserver.server.protocols.web.base_socket_model import BaseSocketModel
from nodeserver.server.protocols.web.messages.server.engine_messages import EngineEventPayloadAdapter
from nodeserver.server.protocols.web.messages.server.server_cmd_responses import CmdResponsePayloadAdapter
from nodeserver.server.protocols.web.messages.server.worker_messages import WorkerEventPayloadAdapter

class ServerMessageTypes(StrEnum):
    SCENE_EVENT = "scene_event"
    GRAPH_EVENT = "graph_event"
    COMMAND_RESPONSE = "cmd_response"

class BaseServerMessage(BaseSocketModel):
    type: ServerMessageTypes


class ServerWorkerEventWrapper(BaseServerMessage):
    type: Literal[ServerMessageTypes.SCENE_EVENT] = ServerMessageTypes.SCENE_EVENT
    event_payload: WorkerEventPayloadAdapter

class ServerEngineEventWrapper(BaseServerMessage):
    type: Literal[ServerMessageTypes.GRAPH_EVENT] = ServerMessageTypes.GRAPH_EVENT
    event_payload: EngineEventPayloadAdapter

class ServerCmdResponse(BaseServerMessage):
    type: Literal[ServerMessageTypes.COMMAND_RESPONSE] = ServerMessageTypes.COMMAND_RESPONSE
    cmd_uid: str
    response_payload: CmdResponsePayloadAdapter
