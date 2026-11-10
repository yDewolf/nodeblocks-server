from nodeblocks.generated.server import command_responses_pb2
from nodeblocks.protocols.utils.scene_data_protoc_serialize import serialize_scene_data
from nodeblocks.server.protocols.web.messages.server.server_cmd_responses import AddConnPayload, AddNodePayload, ExecutionStateSyncPayload, GetSceneDataPayload


def serialize_cmd_response(response_payload, cmd_uid: str, status_obj) -> command_responses_pb2.ServerCmdResponseMessage:
    proto_cmd = command_responses_pb2.ServerCmdResponseMessage()
    proto_cmd.type = str(response_payload.type)
    proto_cmd.request_id = cmd_uid

    if status_obj:
        proto_cmd.status.status = str(status_obj.status)
        proto_cmd.status.message = status_obj.message or ""

    if isinstance(response_payload, ExecutionStateSyncPayload):
        proto_cmd.execution_state_sync.state = str(response_payload.state)
        proto_cmd.execution_state_sync.mode = str(response_payload.mode)
        if response_payload.target_nodes:
            proto_cmd.execution_state_sync.target_nodes.extend(response_payload.target_nodes)
        if response_payload.target_iterations is not None:
            proto_cmd.execution_state_sync.target_iterations = response_payload.target_iterations

    elif isinstance(response_payload, AddNodePayload):
        if response_payload.nodes:
            proto_cmd.add_node.nodes.extend(response_payload.nodes)

    elif isinstance(response_payload, AddConnPayload):
        if response_payload.conns:
            proto_cmd.add_conn.conns.extend(response_payload.conns)

    elif isinstance(response_payload, GetSceneDataPayload):
        if response_payload.scene_data:
            proto_cmd.get_scene_data.scene_data.CopyFrom(
                serialize_scene_data(response_payload.scene_data)
            )

    return proto_cmd
