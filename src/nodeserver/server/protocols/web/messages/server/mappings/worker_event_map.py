from nodeserver.engine.workers.protocols.general_worker_protocol import EvtFatalError, EvtWorkerReady, EvtWorkerStopped, WorkerEvent
from nodeserver.server.protocols.web.messages.server.worker_messages import WorkerEventPayloadAdapter, WorkerFatalErrorPayload, WorkerReadyPayload, WorkerStoppedPayload


SERVER_ENGINE_EVENT_MAP: dict[type[WorkerEvent], type[WorkerEventPayloadAdapter]] = {
   EvtWorkerReady: WorkerReadyPayload,
   EvtWorkerStopped: WorkerStoppedPayload,
   EvtFatalError: WorkerFatalErrorPayload
}

def get_worker_event_payload(event: WorkerEvent) -> WorkerEventPayloadAdapter:
    payload_type = get_worker_event_payload_type(event.__class__)
    payload = payload_type.model_validate(event.__dict__)
    return payload

def get_worker_event_payload_type(event: type[WorkerEvent]) -> type[WorkerEventPayloadAdapter]:
    payload_type = SERVER_ENGINE_EVENT_MAP.get(event, None)
    if not payload_type:
        super_type = type(event.__class__)
        if issubclass(super_type, WorkerEvent):
            payload_type = get_worker_event_payload_type(super_type)

    if not payload_type:
        raise Exception("Couldn't find payload type for engine event: ", event)
    
    return payload_type
