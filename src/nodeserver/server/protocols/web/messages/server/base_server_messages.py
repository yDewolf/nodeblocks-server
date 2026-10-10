from enum import StrEnum
from typing import Any, Literal, Optional

from nodeserver.engine.runtime.protocols.engine_events import IPCEngineEvent
from nodeserver.engine.workers.protocols.general_worker_protocol import WorkerEvent
from nodeserver.engine.workers.scene.protocols.scene_worker_protocol import IPCSceneWorkerEvent
from nodeserver.server.protocols.web.base_socket_model import BaseSocketModel
from nodeserver.engine.workers.protocols.ipc_protocol import IPCCommandResponse
from nodeserver.server.protocols.web.messages.server.engine_messages import EngineEventPayloadAdapter
from nodeserver.server.protocols.web.messages.server.server_cmd_responses import CmdResponsePayloadAdapter

class ServerMessageTypes(StrEnum):
    SCENE_EVENT = "scene_event"
    GRAPH_EVENT = "graph_event"
    COMMAND_RESPONSE = "cmd_response"

class BaseServerMessage(BaseSocketModel):
    type: ServerMessageTypes

class ServerWorkerEventWrapper(BaseServerMessage):
    type: Literal[ServerMessageTypes.SCENE_EVENT] = ServerMessageTypes.SCENE_EVENT
    event: str # TODO: trocar isso por um enum
    data: Optional[WorkerEvent] = None

class ServerEngineEventWrapper(BaseServerMessage):
    type: Literal[ServerMessageTypes.GRAPH_EVENT] = ServerMessageTypes.GRAPH_EVENT
    event_payload: EngineEventPayloadAdapter

class ServerCmdResponse(BaseServerMessage):
    type: Literal[ServerMessageTypes.COMMAND_RESPONSE] = ServerMessageTypes.COMMAND_RESPONSE
    cmd_uid: str
    response_payload: CmdResponsePayloadAdapter
