from nodeserver.generated.server import worker_messages_pb2
from nodeserver.server.protocols.web.messages.server.worker_messages import WorkerFatalErrorPayload, WorkerReadyPayload, WorkerStoppedPayload


def serialize_worker_event(event_payload) -> worker_messages_pb2.WorkerEventMessage:
    proto_worker = worker_messages_pb2.WorkerEventMessage()
    if isinstance(event_payload, WorkerReadyPayload):
        proto_worker.type = worker_messages_pb2.READY
    
    elif isinstance(event_payload, WorkerStoppedPayload):
        proto_worker.type = worker_messages_pb2.STOPPED

    elif isinstance(event_payload, WorkerFatalErrorPayload):
        proto_worker.type = worker_messages_pb2.FATAL_ERROR
        proto_worker.error = event_payload.error
    
    return proto_worker
