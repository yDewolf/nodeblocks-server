
from abc import ABC, abstractmethod
import logging
from typing import Any, Optional

from pydantic import ValidationError

from nodeserver.engine.exceptions.runtime_exceptions import NodeParamRuntimeError, NodeSlotRuntimeError, extract_ids_and_messages
from nodeserver.engine.helpers.engine_runtime_helper import EngineRuntimeHelper
from nodeserver.engine.protocols.node.logic_nodes import BaseNode, NodeOutputs
from nodeserver.engine.protocols.node.node_instance import NodeInstance
from nodeserver.engine.runtime.extra_node_io import ContextAwareInput
from nodeserver.engine.runtime.protocols.engine_events import NodeExecutionStatus
from nodeserver.engine.runtime.job_runtime_context import EngineRuntimeContext
from nodeserver.engine.runtime.protocols.engine_events import EngineError
from nodeserver.engine.runtime.protocols.engine_tracker import EngineTracker

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
        context.update_node_status(node_instance.uid, NodeExecutionStatus.SUCCESS, result=cached_data["outputs"])

    
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
            context.add_error(EngineError(
                tracker=EngineTracker.node(node_instance.uid),
                message="Failed to find a logic instance for node"
            ))
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

            self._handle_param_update(logic_node, node_instance.uid)
            raw_inputs = self._resolve_inputs(node_instance, context)
            self._inject_context_inputs(raw_inputs, logic_node, context)

            node_inputs = self._handle_create_input_model(logic_node, raw_inputs, node_instance.uid)
            
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

        except NodeParamRuntimeError as e:
            for idx, param_id in enumerate(e.param_ids):
                context.add_error(EngineError(
                    tracker=EngineTracker.param(node_instance.uid, param_id),
                    message=f"Error in parameter '{param_id}' -> {e.messages[idx]}"
                ))
            
            return False

        except NodeSlotRuntimeError as e:
            for idx, slot_id in enumerate(e.slot_ids):
                context.add_error(EngineError(
                    tracker=EngineTracker.slot(node_instance.uid, slot_id),
                    message=f"Error in slot '{slot_id}' -> {e.messages[idx]}"
                ))
            
            return False

        except Exception as e:
            context.add_error(EngineError(
                tracker=EngineTracker.node(node_instance.uid),
                message=str(e)
            ))
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

    def _handle_param_update(self, logic_node: BaseNode, node_uid: str):
        try:
            logic_node._ensure_parameters_updated()
        except ValidationError as e:
            param_ids, error_messages = extract_ids_and_messages(e)
            raise NodeParamRuntimeError(
                node_uid=node_uid,
                param_ids=param_ids,
                messages=error_messages
            )

    def _handle_create_input_model(self, logic_node: BaseNode, raw_inputs: dict[str, Any], node_uid: str):
        try:
            return logic_node.InputModel(**raw_inputs)
        
        except ValidationError as e:
            slot_ids, error_messages = extract_ids_and_messages(e)
            raise NodeSlotRuntimeError(
                messages=error_messages,
                node_uid=node_uid,
                slot_ids=slot_ids,
            )
