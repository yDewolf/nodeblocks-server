import hashlib
import json

from nodeserver.engine.protocols.node.node_instance import NodeInstance
from nodeserver.engine.runtime.runtime_context import GraphRunContext, NodeExecutionStatus


class EngineRuntimeHelper:

    @staticmethod
    def _compute_node_hash(node_instance: NodeInstance, context: GraphRunContext) -> str:
        state_dict = {
            "type_id": node_instance.type_id,
            "params": node_instance.node_data.data,
            "input_hashes": {}
        }

        incoming_connections = context.scene.graph.get_node_connections(node_instance.uid)
        for slot_id, slot in node_instance.slots.items():
            if not slot.is_input:
                continue

            slot_connections = [conn for conn in incoming_connections if conn.to_slot.slot_id == slot_id]
            if slot.spec.max_connections == 0 or slot.spec.max_connections > 1:
                hashes: list[str] = []
                # This assumes that connections are ordered by indexing order
                # nodes that are order dependent (like concatenate) needs a future
                # implementation of connection ordering (TODO)
                for conn in slot_connections:
                    upstream_uid = conn.from_slot.node_id
                    hashes.append(context.node_hashes.get(upstream_uid, "none"))

                state_dict["input_hashes"][slot_id] = hashes
                continue

            if slot_connections:
                upstream_uid = slot_connections[0].from_slot.node_id
                state_dict["input_hashes"][slot_id] = context.node_hashes.get(upstream_uid, "none")
                continue

            state_dict["input_hashes"][slot_id] = None

        state_json = json.dumps(state_dict, sort_keys=True)
        return hashlib.sha256(state_json.encode('utf-8')).hexdigest()

    @staticmethod
    def _has_failed_dependencies(node_uid: str, context: GraphRunContext) -> bool:
        incoming_connections = [
            conn for conn in context.scene.graph.all_connections.values() 
            if conn.to_slot.node_id == node_uid
        ]
        
        for conn in incoming_connections:
            source_node_id = conn.from_slot.node_id
            source_status = context.node_status.get(source_node_id)
            if source_status in (NodeExecutionStatus.FAILED, NodeExecutionStatus.SKIPPED):
                return True
        return False
    