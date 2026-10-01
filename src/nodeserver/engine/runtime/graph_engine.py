import logging
from typing import Any, Optional

from nodeserver.engine.helpers.engine_runtime_helper import EngineRuntimeHelper
from nodeserver.engine.protocols.node.logic_nodes import BaseNode, NodeOutputs
from nodeserver.engine.protocols.node.node_instance import NodeInstance
from nodeserver.engine.runtime.engine_events import JobStatus, NodeExecutionStatus
from nodeserver.engine.runtime.extra_node_io import ContextAwareInput
from nodeserver.engine.runtime.runtime_context import GraphRunContext

logger = logging.getLogger("nds.engine")

# TODO: definir melhor os modos de execuçao da engine 
# e como isso afeta o contexto
class StatelessGraphEngine:

    def execute_subgraph(
        self,
        context: GraphRunContext,
        target_nodes: list[str],
        reraise_exception: bool = False
    ) -> GraphRunContext:
        return self.execute_job(context, target_nodes, reraise_exception)

    def execute_job(
        self, 
        context: GraphRunContext, 
        target_node_uids: Optional[list[str]] = None,
        reraise_exception: bool = False
    ) -> GraphRunContext:
        
        context.set_job_status(JobStatus.RUNNING)
        try:
            execution_order = context.scene.graph.get_topological_order()
            if target_node_uids:
                execution_order = self._filter_execution_order(execution_order, target_node_uids, context)
            
            context.prepare_for_run(execution_order)
            
            ordered_instances = [
                context.scene.graph.ensure_node(node_uid) for node_uid in execution_order
            ]
            for node_instance in ordered_instances:
                self._execute_node(node_instance, context)

            evaluated_statuses = context.node_status.values() if not target_node_uids else [context.node_status[node_uid] for node_uid in execution_order]
            if any(status == NodeExecutionStatus.FAILED for status in evaluated_statuses):
                context.set_job_status(JobStatus.PARTIAL_SUCCESS)
            else:
                context.set_job_status(JobStatus.COMPLETED)
        
        except Exception as e:
            logger.error(f"Fatal error on job {context.job_id}: {e}")
            context.set_job_status(JobStatus.FAILED)
            if reraise_exception: raise e
        
        return context

    # Execution utils:

    def _execute_node(self, node_instance: NodeInstance, context: GraphRunContext):
        if EngineRuntimeHelper._has_failed_dependencies(node_instance.uid, context):
            context.update_node_status(
                node_instance.uid, NodeExecutionStatus.SKIPPED
            )
            return
        
        success = self._process_node(node_instance, context)
        if not success:
            context.update_node_status(
                node_instance.uid, NodeExecutionStatus.FAILED
            )
            return

        cached_data = context.persistent_cache.get(node_instance.uid, {})
        outputs = cached_data.get("outputs", {})
        
        context.update_node_status(
            node_instance.uid, 
            NodeExecutionStatus.SUCCESS, 
            result=outputs
        )

    def _filter_execution_order(self, execution_order: list[str], target_node_uids: list[str], context: GraphRunContext):
        required_uids = set()
        for target_uid in target_node_uids:
            required_uids.add(target_uid)
            required_uids.update(context.scene.graph.get_upstream_node_ids(target_uid))
        
        
        return [id for id in execution_order if id in required_uids]

    
    # Utility
    
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
            node_outputs: NodeOutputs = logic_node.forward(node_inputs)

            # slot_id -> output_value
            outputs_dict: dict[str, Any] = {}
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

            if values:
                raw_inputs[slot_id] = values[0]
        
        return raw_inputs
