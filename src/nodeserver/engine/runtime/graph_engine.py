import logging
from typing import Any

from nodeserver.engine.helpers.engine_runtime_helper import EngineRuntimeHelper
from nodeserver.engine.helpers.graph_helper import NodeGraphHelper
from nodeserver.engine.protocols.logic_nodes import BaseNode
from nodeserver.engine.protocols.node_instance import NodeInstance
from nodeserver.engine.runtime.extra_node_io import ContextAwareInput
from nodeserver.engine.runtime.runtime_context import GraphRunContext, JobStatus, NodeExecutionStatus

logger = logging.getLogger("nds.engine")

class StatelessGraphEngine:
    def execute_job(self, context: GraphRunContext) -> GraphRunContext:
        context.status = JobStatus.RUNNING
        
        try:
            execution_order = NodeGraphHelper._get_execution_order(context.scene)
            for node_instance in execution_order:
                if EngineRuntimeHelper._has_failed_dependencies(node_instance.uid, context):
                    context.node_status[node_instance.uid] = NodeExecutionStatus.SKIPPED
                    continue
                
                success = self._process_node(node_instance, context)
                if success:
                    context.node_status[node_instance.uid] = NodeExecutionStatus.SUCCESS
                    continue
                
                context.node_status[node_instance.uid] = NodeExecutionStatus.FAILED

            if any(status == NodeExecutionStatus.FAILED for status in context.node_status.values()):
                context.status = JobStatus.PARTIAL_SUCCESS
            else:
                context.status = JobStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Erro fatal no Job {context.job_id}: {e}")
            context.status = JobStatus.FAILED
        
        return context

    def _process_node(self, node_instance: NodeInstance, context: GraphRunContext) -> bool:
        logic_node = context.scene._logic_nodes.get(node_instance.uid)
        if not logic_node:
            context.errors[node_instance.uid] = "Failed to find a logic instance for node"
            return False

        try:
            current_hash = EngineRuntimeHelper._compute_node_hash(node_instance, context)
            context.node_hashes[node_instance.uid] = current_hash

            if not logic_node.config.bypass_cache:
                cached_data = context.persistent_cache.get(node_instance.uid)
                
                if cached_data and cached_data.get("hash") == current_hash:
                    cached_outputs = cached_data["outputs"]
                    for slot_id, value in cached_outputs.items():
                        # Map persistent cached data to output cache (so dependent nodes can use it)
                        cache_key = context.get_cache_key(node_instance.uid, slot_id)
                        context.output_cache[cache_key] = value
                    
                    return True

            logic_node._ensure_parameters_updated()
            
            raw_inputs = self._resolve_inputs(node_instance, context)
            self._inject_context_inputs(raw_inputs, logic_node, context)
            
            node_inputs = logic_node.InputModel(**raw_inputs)
            
            logic_node.pre_forward(node_inputs)
            node_outputs = logic_node.forward(node_inputs)

            outputs_dict = {}
            for slot_id, value in node_outputs.__dict__.items():
                cache_key = context.get_cache_key(node_instance.uid, slot_id)
                context.output_cache[cache_key] = value
                outputs_dict[slot_id] = value

            # Cache update
            context.persistent_cache[node_instance.uid] = {
                "hash": current_hash,
                "outputs": outputs_dict
            }

            logic_node.post_forward_cleanup()
            return True
            
        except Exception as e:
            context.errors[node_instance.uid] = str(e)
            return False
    
    # Utility

    # TODO: talvez implementar um registro de funções que injetam informações
    # nos inputs do node
    def _inject_context_inputs(self, raw_inputs: dict[str, Any], logic_instance: BaseNode, context: GraphRunContext):
        if isinstance(logic_instance.InputModel, ContextAwareInput):
            raw_inputs["context"] = context


    def _resolve_inputs(self, node_instance: NodeInstance, context: GraphRunContext) -> dict[str, Any]:
        raw_inputs = {}
        
        incoming_connections = context.scene.graph.get_node_connections(node_instance.uid)
        for slot_id, slot in node_instance.slots.items():
            if not slot.is_input:
                continue

            slot_connections = [conn for conn in incoming_connections if conn.to_slot.slot_id == slot_id]

            values: list[Any] = []
            for conn in slot_connections:
                cache_key = context.get_cache_key(conn.from_slot.node_id, conn.from_slot.slot_id)
                if cache_key in context.output_cache:
                    values.append(context.output_cache[cache_key])
            
            if slot.spec.max_connections != 0:
                values = values[:slot.spec.max_connections]
                
            if slot.spec.max_connections == 0: # unlimited connections
                raw_inputs[slot_id] = values
                continue

            raw_inputs[slot_id] = values[0] if values else None
        
        return raw_inputs
