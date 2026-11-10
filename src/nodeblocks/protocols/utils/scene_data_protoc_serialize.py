import json

from nodeblocks.generated.protocols import scene_data_pb2
from nodeblocks.protocols.manifest.node.node_graph import SceneData

def serialize_scene_data(scene_data_obj: SceneData) -> scene_data_pb2.SceneDataMessage:
    proto_scene = scene_data_pb2.SceneDataMessage()
    proto_scene.uid = scene_data_obj.uid

    for pkg_id, version in scene_data_obj.dependencies.items():
        proto_scene.dependencies[pkg_id] = version

    for node_id, node_data in scene_data_obj.nodes.items():
        proto_node = scene_data_pb2.NodeSceneDataMessage()
        proto_node.uid = node_data.uid
        proto_node.nodetype_fqn = node_data.nodetype_fqn
        
        proto_node.position.x = node_data.position.x
        proto_node.position.y = node_data.position.y

        if node_data.data:
            for param_id, param_value in node_data.data.items():
                proto_node.data[param_id] = json.dumps(param_value) if not isinstance(param_value, str) else param_value

        proto_scene.nodes[node_id].CopyFrom(proto_node)

    for conn_id, conn_data in scene_data_obj.connections.items():
        proto_conn = scene_data_pb2.ConnectionSceneDataMessage()
        proto_conn.uid = conn_data.uid

        proto_conn.from_slot.node_id = conn_data.from_slot.node_id
        proto_conn.from_slot.slot_id = conn_data.from_slot.slot_id

        proto_conn.to_slot.node_id = conn_data.to_slot.node_id
        proto_conn.to_slot.slot_id = conn_data.to_slot.slot_id

        proto_scene.connections[conn_id].CopyFrom(proto_conn)

    return proto_scene
