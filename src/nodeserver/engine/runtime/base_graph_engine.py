
from abc import ABC, abstractmethod
import logging
from typing import Any, Optional

from nodeserver.engine.helpers.engine_runtime_helper import EngineRuntimeHelper
from nodeserver.engine.protocols.node.logic_nodes import BaseNode, NodeOutputs
from nodeserver.engine.protocols.node.node_instance import NodeInstance
from nodeserver.engine.runtime.extra_node_io import ContextAwareInput
from nodeserver.engine.runtime.protocols.engine_context import NodeExecutionStatus
from nodeserver.engine.runtime.job_runtime_context import EngineRuntimeContext

logger = logging.getLogger("nds.engine")

class BaseGraphEngine(ABC):
    @abstractmethod
    def execute_subgraph(
        self,
        context: EngineRuntimeContext,
        reraise_exception: bool = False
    ) -> EngineRuntimeContext:
        pass

    @abstractmethod
    def execute_graph(
        self,        
        context: EngineRuntimeContext,
        reraise_exception: bool = False
    ) -> EngineRuntimeContext:
        pass



    def _execute_nodes(self, context: EngineRuntimeContext, target_nodes: Optional[list[str]], execution_order: Optional[list[str]] = None):
        execution_order = execution_order or context.scene.graph.get_topological_order()
        if target_nodes:
            execution_order = self._filter_execution_order(
                execution_order, target_nodes, context
            )
        
        ordered_instances = [
            context.scene.graph.ensure_node(node_uid) for node_uid in execution_order
        ]
        
        for node_instance in ordered_instances:
            self._execute_node(node_instance, context)

        return execution_order

    def _execute_node(self, node_instance: NodeInstance, context: EngineRuntimeContext):
        if EngineRuntimeHelper._has_failed_dependencies(node_instance.uid, context):
            context.update_node_status(node_instance.uid, NodeExecutionStatus.SKIPPED)
            return
        
        success = self._process_node(node_instance, context)
        if not success:
            context.update_node_status(node_instance.uid, NodeExecutionStatus.FAILED)
            return

        cached_data = context.persistent_cache.get(node_instance.uid, {})
        context.update_node_status(node_instance.uid, NodeExecutionStatus.SUCCESS, result=cached_data)

    
    def _filter_execution_order(self, execution_order: list[str], target_node_uids: list[str], context: EngineRuntimeContext) -> list[str]:
        required_uids = set()
        for target_uid in target_node_uids:
            required_uids.add(target_uid)
            required_uids.update(context.scene.graph.get_upstream_node_ids(target_uid))
        
        return [uid for uid in execution_order if uid in required_uids]


    # Internal utilities

    def _process_node(self, node_instance: NodeInstance, context: EngineRuntimeContext) -> bool:
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
                        cache_key = context.get_cache_key(node_instance.uid, slot_id)
                        context.output_cache[cache_key] = value
                    
                    return True

            logic_node._ensure_parameters_updated()
            
            raw_inputs = self._resolve_inputs(node_instance, context)
            self._inject_context_inputs(raw_inputs, logic_node, context)
            
            node_inputs = logic_node.InputModel(**raw_inputs)
            
            logic_node.pre_forward(node_inputs)
            node_outputs: NodeOutputs = logic_node.forward(node_inputs)

            outputs_dict: dict[str, Any] = {}
            for slot_id, value in node_outputs.__dict__.items():
                cache_key = context.get_cache_key(node_instance.uid, slot_id)
                context.output_cache[cache_key] = value
                outputs_dict[slot_id] = value

            context.persistent_cache[node_instance.uid] = {
                "hash": current_hash,
                "outputs": outputs_dict
            }

            logic_node.post_forward_cleanup()
            return True
            
        except Exception as e:
            context.errors[node_instance.uid] = str(e)
            return False

    def _inject_context_inputs(
        self, 
        raw_inputs: dict[str, Any], 
        logic_instance: BaseNode, 
        context: EngineRuntimeContext
    ):
        if isinstance(logic_instance.InputModel, ContextAwareInput):
            raw_inputs["context"] = context

    def _resolve_inputs(
        self, 
        node_instance: NodeInstance, 
        context: EngineRuntimeContext
    ) -> dict[str, Any]:
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
                
            if slot.spec.max_connections == 0: 
                raw_inputs[slot_id] = values
                continue

            if values:
                raw_inputs[slot_id] = values[0]
        
        return raw_inputs
