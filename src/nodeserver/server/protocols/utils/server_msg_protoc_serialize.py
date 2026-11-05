import logging
from typing import Optional

from nodeserver.generated.server import server_messages_pb2
from nodeserver.server.protocols.utils.cmd_response_protoc_serialize import serialize_cmd_response
from nodeserver.server.protocols.utils.engine_msg_protoc_serialize import serialize_engine_event
from nodeserver.server.protocols.utils.worker_msg_protoc_serialize import serialize_worker_event
from nodeserver.server.protocols.web.messages.server.server_messages import BaseServerMessage, ServerBatchEventWrapper, ServerCmdResponse, ServerEngineEventWrapper, ServerWorkerEventWrapper

logger = logging.getLogger("nds.server")

def serialize_server_message_to_proto(message: BaseServerMessage) -> Optional[bytes]:
    try:
        if isinstance(message, ServerEngineEventWrapper):
            return serialize_engine_event(message.event_payload)

        elif isinstance(message, ServerWorkerEventWrapper):
            wrapper = server_messages_pb2.ServerMessageWrapper()
            wrapper.worker_event.CopyFrom(serialize_worker_event(message.event_payload))
            return wrapper.SerializeToString()

        elif isinstance(message, ServerCmdResponse):
            wrapper = server_messages_pb2.ServerMessageWrapper()
            status_obj = getattr(message.response_payload, "status", None)
            wrapper.cmd_response.CopyFrom(serialize_cmd_response(message.response_payload, message.cmd_uid, status_obj))
            return wrapper.SerializeToString()

        elif isinstance(message, ServerBatchEventWrapper):
            batch_proto = server_messages_pb2.ServerBatchMessage()
            for sub_msg in message.messages:
                serialized_bytes = serialize_server_message_to_proto(sub_msg)
                if serialized_bytes:
                    wrapped_item = server_messages_pb2.ServerMessageWrapper()
                    wrapped_item.ParseFromString(serialized_bytes)
                    batch_proto.messages.append(wrapped_item)
            
            return batch_proto.SerializeToString()

    except Exception as e:
        logger.error("Failed to serialize message to protobuf, falling back to JSON: %s", e)
        return None

    return None
