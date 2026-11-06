from nodeserver.generated.server import engine_messages_pb2
from nodeserver.protocols.utils.datatype_value_protoc_serialize import serialize_datatype_value
from nodeserver.server.protocols.web.messages.server.engine_messages import EngineEventPayload, FailedProcessPayload, JobStatusPayload, NodeStatusPayload, RuntimeErrorPayload


def serialize_engine_event(pydantic_event: EngineEventPayload) -> engine_messages_pb2.EngineEventMessage:
    proto_msg = engine_messages_pb2.EngineEventMessage()
    proto_msg.job_id = pydantic_event.job_id
    
    if pydantic_event.tracker:
        if pydantic_event.tracker.node_id:
            proto_msg.tracker.node_id = pydantic_event.tracker.node_id

        if pydantic_event.tracker.slot_id:
            proto_msg.tracker.slot_id = pydantic_event.tracker.slot_id

        if pydantic_event.tracker.param_id:
            proto_msg.tracker.param_id = pydantic_event.tracker.param_id

        if pydantic_event.tracker.conn_id:
            proto_msg.tracker.conn_id = pydantic_event.tracker.conn_id

        if pydantic_event.tracker.other:
            for key, value in pydantic_event.tracker.other.items():
                proto_msg.tracker.other[key] = value

    if isinstance(pydantic_event, NodeStatusPayload):
        proto_msg.type = engine_messages_pb2.NODE_STATUS
        proto_msg.node_status.node_uid = pydantic_event.node_uid
        proto_msg.node_status.status = pydantic_event.status.value

        if pydantic_event.node_result:
            for key, value in pydantic_event.node_result.items():
                proto_msg.node_status.node_result[key].CopyFrom(
                    serialize_datatype_value(value)
                )

    elif isinstance(pydantic_event, JobStatusPayload):
        proto_msg.type = engine_messages_pb2.JOB_STATUS
        proto_msg.job_status.status = pydantic_event.status.value

    elif isinstance(pydantic_event, FailedProcessPayload):
        proto_msg.type = engine_messages_pb2.FAILED_PROCESS
        proto_msg.failed_process.error = pydantic_event.error

    elif isinstance(pydantic_event, RuntimeErrorPayload):
        proto_msg.type = engine_messages_pb2.RUNTIME_ERROR
        proto_msg.runtime_error.message = pydantic_event.message

    return proto_msg
