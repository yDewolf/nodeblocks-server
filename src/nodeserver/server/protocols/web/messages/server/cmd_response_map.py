from nodeserver.engine.workers.protocols.ipc_protocol import IPCCommandResponse
from nodeserver.engine.workers.scene.protocols.scene_worker_protocol import AddConnCommandResponse, AddNodeCommandResponse, CheckExecutionStateResponse, GetSceneDataResponse, SceneWorkerCommandResponse
from nodeserver.server.protocols.web.messages.server.server_cmd_responses import AddConnPayload, AddNodePayload, CmdResponsePayloadAdapter, CommandResponsePayload, ExecutionCheckPayload, GenericCommandPayload, GetSceneDataPayload

# TODO: pensar em um jeito melhor de mapear isso aqui
SERVER_CMD_RESPONSE_MAP: dict[type[IPCCommandResponse], type[CmdResponsePayloadAdapter]] = {
    SceneWorkerCommandResponse: GenericCommandPayload,

    CheckExecutionStateResponse: ExecutionCheckPayload,
    AddNodeCommandResponse: AddNodePayload,
    AddConnCommandResponse: AddConnPayload,
    GetSceneDataResponse: GetSceneDataPayload
}

def get_response_payload(response: IPCCommandResponse) -> CmdResponsePayloadAdapter:
    payload_type = get_response_payload_type(response.__class__)
    payload = payload_type.model_validate(response.__dict__)
    return payload

def get_response_payload_type(response: type[IPCCommandResponse]) -> type[CmdResponsePayloadAdapter]:
    payload_type = SERVER_CMD_RESPONSE_MAP.get(response, None)
    if not payload_type:
        super_type = type(response.__class__)
        if issubclass(super_type, SceneWorkerCommandResponse):
            payload_type = get_response_payload_type(super_type)

    if not payload_type:
        raise Exception("Couldn't find payload type for command: ", response)
    
    return payload_type
