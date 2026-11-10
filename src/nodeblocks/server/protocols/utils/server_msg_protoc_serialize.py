import logging
from typing import Optional

from nodeblocks.generated.server import server_messages_pb2
from nodeblocks.server.protocols.utils.cmd_response_protoc_serialize import serialize_cmd_response
from nodeblocks.server.protocols.utils.engine_msg_protoc_serialize import serialize_engine_event
from nodeblocks.server.protocols.utils.worker_msg_protoc_serialize import serialize_worker_event
from nodeblocks.server.protocols.web.messages.server.server_messages import BaseServerMessage, ServerBatchEventWrapper, ServerCmdResponse, ServerEngineEventWrapper, ServerWorkerEventWrapper

logger = logging.getLogger("nds.server")


def serialize_server_msg_to_bytes(message: BaseServerMessage) -> Optional[bytes]:
    try:
        proto = server_msg_to_proto(message)
        if proto:
            return proto.SerializeToString()

        return None
    
    except Exception as e:
        logger.error("Failed to serialize message to protobuf, falling back to JSON: %s", e)
        return None

def server_msg_to_proto(message: BaseServerMessage) -> Optional[server_messages_pb2.ServerMessageWrapper]:
    try:
        wrapper = server_messages_pb2.ServerMessageWrapper()
        if isinstance(message, ServerBatchEventWrapper):
            wrapper.type = server_messages_pb2.BATCH
            for sub_msg in message.messages:
                batch_item = server_messages_pb2.ServerBatchItemMessage()
                batch_item = populate_wrapper(batch_item, sub_msg)
                if not batch_item: raise Exception(f"Failed to populate BatchItemMessage. sub_msg: {sub_msg}")
                wrapper.batch.messages.append(batch_item)
        else:
            wrapper = populate_wrapper(wrapper, message)        

        return wrapper

    except Exception as e:
        logger.error("Failed to generate proto from server msg. %s", e)
        raise e


def populate_wrapper(wrapper: server_messages_pb2.ServerMessageWrapper | server_messages_pb2.ServerBatchItemMessage, message: BaseServerMessage):
    if isinstance(message, ServerWorkerEventWrapper):
        if isinstance(wrapper, server_messages_pb2.ServerMessageWrapper):
            wrapper.type = server_messages_pb2.SCENE_EVENT
        
        wrapper.scene_event.event_payload.CopyFrom(serialize_worker_event(message.event_payload))
        
    elif isinstance(message, ServerEngineEventWrapper):
        if isinstance(wrapper, server_messages_pb2.ServerMessageWrapper):
            wrapper.type = server_messages_pb2.GRAPH_EVENT

        wrapper.graph_event.event_payload.CopyFrom(serialize_engine_event(message.event_payload))
        
    elif isinstance(message, ServerCmdResponse):
        if isinstance(wrapper, server_messages_pb2.ServerMessageWrapper):
            wrapper.type = server_messages_pb2.COMMAND_RESPONSE
    
        wrapper.cmd_response.cmd_uid = message.cmd_uid
        status_obj = getattr(message.response_payload, "status", None)
        wrapper.cmd_response.response_payload.CopyFrom(
            serialize_cmd_response(message.response_payload, message.cmd_uid, status_obj)
        )

    else:
        return None

    return wrapper