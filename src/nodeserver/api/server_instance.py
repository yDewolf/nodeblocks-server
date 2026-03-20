
import logging
from typing import Callable
from nodeserver.api.base_nodes import BaseNode
from nodeserver.api.node_scene import NodeScene

# TODO: make a node_scene class with every node and connections + other things related to the scene
INSTANCE_LOGGER = logging.Logger("InstanceLogger")

class BaseServerRuntime:
    _current_idx: int | None = None
    _process_order: list[int] | None = None
    waiting_for_continue: bool
    
    def __init__(self):
        self.waiting_for_continue = False

        
    def process_next(self, node_scene: NodeScene) -> tuple[dict | None, BaseNode] | None:
        if self._current_idx == None or not self._process_order:
            return None
        
        if self._current_idx >= len(self._process_order):
            self.waiting_for_continue = True
            return None
        
        current_node = node_scene.get_node(self._process_order[self._current_idx])
        if current_node == None:
            return None
        
        self._current_idx += 1
        
        # TODO: Node Input
        node_input = None
        result = current_node.forward(node_input)
        return (result, current_node)

    def continue_process(self, scene: NodeScene):
        self.waiting_for_continue = False
        self.on_scene_changed(scene)

    
    def validate_scene(self, node_scene: NodeScene):
        pass


    def on_scene_changed(self, new_scene: NodeScene):
        # TODO: Actually check if the order is fine based on connections
        self._process_order = [
            node._mirror.id for node in new_scene.nodes
        ]
        
        self._current_idx = 0
        if len(self._process_order) == 0:
            self._current_idx = None


# TODO:
class ServerInstance:
    _attributed_id: str = ""
    _runtime: BaseServerRuntime
    _on_output: Callable[[dict], None] | None = None

    running: bool = False
    auto_loop: bool = True
    
    loaded_scene: NodeScene | None = None

    def __init__(self):
        self.setup()

    def setup(self):
        self._runtime = BaseServerRuntime()


    def runtime_tick(self):
        if not self.running:
            return

        if not self.loaded_scene:
            return

        # TODO: Check if it should actually continue
        if self._runtime.waiting_for_continue and self.auto_loop:
            self._runtime.continue_process(self.loaded_scene)

        results = self._runtime.process_next(self.loaded_scene)
        if results != None and self._on_output != None:
            result, node = results
            self._on_output({
                "type": "node_output",
                "node_id": node._mirror.id,
                "value": result
            })
            
        INSTANCE_LOGGER.info("DEBUG: Running server instance")

    # TODO:
    def set_output_callback(self, callback: Callable[[dict], None]):
        self._on_output = callback


    def start_running(self):
        self.running = True

    def stop_running(self):
        self.running = False


    def _scene_changed(self, scene: NodeScene):
        self.loaded_scene = scene
        self._runtime.on_scene_changed(scene)

    def save_state(self):
        pass

    def load_state(self, something):
        pass