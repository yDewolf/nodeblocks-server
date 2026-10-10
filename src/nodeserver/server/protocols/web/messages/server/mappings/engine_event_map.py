


from nodeserver.engine.runtime.protocols.engine_events import EvtFailedProcess, EvtJobStatusChanged, EvtNodeStatusChanged, IPCEngineEvent
from nodeserver.server.protocols.web.messages.server.engine_messages import EngineEventPayloadAdapter, FailedProcessPayload, JobStatusPayload, NodeStatusPayload

# TODO: find a better way of mapping these event to the respective payloads
SERVER_ENGINE_EVENT_MAP: dict[type[IPCEngineEvent], type[EngineEventPayloadAdapter]] = {
    EvtNodeStatusChanged: NodeStatusPayload,
    EvtJobStatusChanged: JobStatusPayload,
    EvtFailedProcess: FailedProcessPayload
}

def get_engine_event_payload(event: IPCEngineEvent) -> EngineEventPayloadAdapter:
    payload_type = get_engine_event_payload_type(event.__class__)
    payload = payload_type.model_validate(event.__dict__)
    return payload

def get_engine_event_payload_type(event: type[IPCEngineEvent]) -> type[EngineEventPayloadAdapter]:
    payload_type = SERVER_ENGINE_EVENT_MAP.get(event, None)
    if not payload_type:
        super_type = type(event.__class__)
        if issubclass(super_type, IPCEngineEvent):
            payload_type = get_engine_event_payload_type(super_type)

    if not payload_type:
        raise Exception("Couldn't find payload type for engine event: ", event)
    
    return payload_type
