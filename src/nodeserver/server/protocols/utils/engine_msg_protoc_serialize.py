from nodeserver.generated.server import engine_messages_pb2
from nodeserver.protocols.utils.datatype_value_protoc_serialize import serialize_datatype_value
from nodeserver.server.protocols.web.messages.server.engine_messages import EngineEventPayload, FailedProcessPayload, JobStatusPayload, NodeStatusPayload, RuntimeErrorPayload


def serialize_engine_event(pydantic_event: EngineEventPayload) -> bytes:
    proto_msg = engine_messages_pb2.EngineEventMessage()
    proto_msg.job_id = pydantic_event.job_id

    if isinstance(pydantic_event, NodeStatusPayload):
        proto_msg.type = engine_messages_pb2.NODE_STATUS
        proto_msg.node_status.node_uid = pydantic_event.node_uid
        proto_msg.node_status.status = str(pydantic_event.status)

        if pydantic_event.node_result:
            for slot_id, value in pydantic_event.node_result.items():
                proto_msg.node_status.node_result[slot_id].CopyFrom(
                    serialize_datatype_value(value)
                )

    elif isinstance(pydantic_event, JobStatusPayload):
        proto_msg.type = engine_messages_pb2.JOB_STATUS
        proto_msg.job_status.status = str(pydantic_event.status)

    elif isinstance(pydantic_event, FailedProcessPayload):
        proto_msg.type = engine_messages_pb2.FAILED_PROCESS
        proto_msg.failed_process.error = pydantic_event.error

    elif isinstance(pydantic_event, RuntimeErrorPayload):
        proto_msg.type = engine_messages_pb2.RUNTIME_ERROR
        proto_msg.runtime_error.message = pydantic_event.message

    return proto_msg.SerializeToString()
