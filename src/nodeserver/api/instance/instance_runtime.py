
import logging
from typing import Optional

from pydantic import BaseModel

from nodeserver.api.instance.node_scene import NodeScene
from nodeserver.api.internal.internal_protocols import InstanceProtocol
from nodeserver.api.node.abstract._nodes import _Node
from nodeserver.api.node.abstract._slots import _SlotIO
from nodeserver.api.web.requests.notification_requests import NotificationLevel, ServerNotification
from nodeserver.wrapper.nodes.data.node_data_types import SuperSlotTypes
from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror, SlotMirror
from nodeserver.wrapper.nodes.node.node_utils import NodeMirrorUtils

logger = logging.getLogger("nds.instances")

class _ReadonlyContext:
    _scene: Optional[NodeScene] = None
    _current_idx: int
    _process_order: list[NodeMirror]
    _output_cache: dict[SlotMirror, _SlotIO]

    _node_execution_cache: dict[str, int]

    _processed_nodes: list[_Node]
    @property
    def processed_nodes(self) -> list[_Node]:
        return self._processed_nodes

    def __init__(
            self, 
            scene: Optional[NodeScene], 
            current_idx: int = 0, 
            output_cache: dict[SlotMirror, _SlotIO] = {}, 
            execution_cache: dict[str, int] = {}, 
            process_order: list[NodeMirror] = [], 
            processed_nodes: list[_Node] = [],
    ) -> None:
        self._scene = scene
        
        self._current_idx = current_idx
        self._output_cache = output_cache
        self._node_execution_cache = execution_cache
        self._process_order = process_order
        self._processed_nodes = processed_nodes
    
    def _get_current_node(self, scene: NodeScene) -> Optional[_Node]:
        if self._current_idx == None or not self._process_order:
            return None
        
        if self.finished_loop():
            return None
        
        current_node = scene.get_node(self._process_order[self._current_idx].uid)
        if not isinstance(current_node, _Node):
            raise Exception(f"Node {current_node} doesn't extend {_Node}")
        
        if current_node == None:
            return None
    
        return current_node

    def _get_cached_outputs(self, node: _Node) -> dict[SlotMirror, _SlotIO]:
        return {
            slot: self._output_cache[slot]
            for slot in node._mirror.slots.get(SuperSlotTypes.OUTPUT, [])
            if slot in self._output_cache
        }

    def finished_loop(self) -> bool:
        return self._current_idx >= len(self._process_order)

    def readonly(self):
        return self

class ContextAwareInput(BaseModel):
    class Config:
        arbitrary_types_allowed=True

    _context: Optional[_ReadonlyContext] = None

class RuntimeContext(_ReadonlyContext):
    def __init__(self, scene: NodeScene) -> None:
        super().__init__(
            scene,
            process_order=NodeMirrorUtils.get_node_execution_order(scene.nodes)
        )

    def _reset_cache(self):
        # self._node_execution_cache.clear()
        # self._output_cache.clear()
        self._processed_nodes.clear()
    
    def _add_to_processed(self, node: _Node):
        if self._processed_nodes.__contains__(node):
            raise Exception(f"Node was already processed {node._mirror.uid}")
        
        self._processed_nodes.append(node)

    def _update_outputs(self, node: _Node, outputs: dict) -> dict[SlotMirror, _SlotIO]:
        output_data: dict[SlotMirror, _SlotIO] = {}
        for slot_name in outputs:
            slot = node.slot(slot_name)
            if slot._mirror.type._super_type != SuperSlotTypes.OUTPUT:
                logger.error(f"ERROR: Outputs should always come from an Output slot | Slot: {slot} | Node: {node}")
            
            slot._io.value = outputs[slot_name]
            output_data[slot._mirror] = slot._io
            self._output_cache[slot._mirror] = slot._io

        self._add_to_processed(node)
        return output_data

    def readonly(self):
        return _ReadonlyContext(
            scene=self._scene,
            current_idx=self._current_idx,
            output_cache=self._output_cache,
            execution_cache=self._node_execution_cache,
            process_order=self._process_order,
            processed_nodes=self.processed_nodes
        )

class InstanceRuntime:
    context: Optional[RuntimeContext] = None
    waiting_to_continue: bool
    def __init__(self):
        self.waiting_to_continue = False
        
    def process_next(self, node_scene: NodeScene, instance_protocol: InstanceProtocol) -> Optional[tuple[dict[SlotMirror, _SlotIO] | None, _Node, bool]]:
        if not self.context: return
        if self.context.finished_loop():
            self.waiting_to_continue = True
            return

        current_node = self.context._get_current_node(node_scene)
        if not current_node or self.context._current_idx == None: 
            return
        self.context._current_idx += 1
        
        current_node._ensure_parameters_updated()

        current_hash = current_node.get_execution_hash(self.context._output_cache)
        last_hash = self.context._node_execution_cache.get(current_node._mirror.uid)
        if current_hash == last_hash and not current_node.bypass_cache:
            return (self.context._get_cached_outputs(current_node), current_node, True)

        try:
            raw_node_inputs = current_node.resolve_inputs(self.context._output_cache)
            node_inputs: BaseModel = current_node._parse_inputs(raw_node_inputs)
            if isinstance(node_inputs, ContextAwareInput):
                node_inputs._context = self.context.readonly()
            
            current_node.pre_forward(node_inputs) # Node might set bypass cache to True here
            
            node_output: BaseModel = current_node.forward(node_inputs)
            output_model: dict = node_output.model_dump()
            output_data = self.context._update_outputs(current_node, output_model)

            current_node.post_forward()
            self.context._node_execution_cache[current_node._mirror.uid] = current_hash
            return (output_data, current_node, False)

        except Exception as e:
            logger.error(e)
            instance_protocol.send_to_client(ServerNotification.node_notify(
                node_uid=current_node._mirror.uid,
                message="Something went wrong",
                level=NotificationLevel.ERROR,
                description=str(e)
            ))

    def continue_process(self, scene: NodeScene):
        self.waiting_to_continue = False
        self.on_scene_changed(scene)

    
    def validate_scene(self, node_scene: NodeScene):
        pass

    def on_scene_changed(self, new_scene: NodeScene):
        self.context = RuntimeContext(
            scene=new_scene,
        )
        self.context._reset_cache()