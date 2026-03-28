
import logging
from typing import Callable
from nodeserver.api.base_nodes import BaseNode
from nodeserver.api.node_scene import NodeScene
from nodeserver.networking.nodes.data.node_data_types import SuperSlotTypes
from nodeserver.networking.nodes.helpers.file.typing_file_reader import TypeFileReader
from nodeserver.networking.nodes.helpers.scene_manager import MirrorSceneManager
from nodeserver.networking.nodes.node.base_nodes import NodeMirror, SlotMirror
from nodeserver.networking.nodes.node.node_utils import NodeUtils

# TODO: make a node_scene class with every node and connections + other things related to the scene
INSTANCE_LOGGER = logging.Logger("InstanceLogger")

class BaseServerRuntime:
    _current_idx: int | None = None
    _process_order: list[NodeMirror] | None = None
    _output_cache: dict[SlotMirror, dict]

    _previous_output: dict | None = None
    waiting_for_continue: bool
    
    def __init__(self):
        self.waiting_for_continue = False

        
    def process_next(self, node_scene: NodeScene) -> tuple[dict | None, BaseNode] | None:
        if self._current_idx == None or not self._process_order:
            return None
        
        if self._current_idx >= len(self._process_order):
            self.waiting_for_continue = True
            return None
        
        current_node = node_scene.get_node(self._process_order[self._current_idx].id)
        if current_node == None:
            return None
        
        self._current_idx += 1
        
        # InputSlot -> dict[OutputSlot, output_value]
        node_inputs: dict[SlotMirror, dict[SlotMirror, dict]] = {}
        for slot_type in current_node._mirror.slots:
            if slot_type != SuperSlotTypes.INPUT:
                continue
            for slot in current_node._mirror.slots[slot_type]:
                connections_output = {}
                for connected_slot in slot.connections:
                    connections_output[connected_slot] = self._output_cache.get(connected_slot)

                node_inputs[slot] = connections_output

        node_result = current_node.forward(node_inputs)
        output_data: dict[SlotMirror, dict] = {}
        for slot in node_result:
            if slot.type._super_type != SuperSlotTypes.OUTPUT:
                INSTANCE_LOGGER.error(f"ERROR: Outputs should always come from an Output slot | Slot: {slot} | Node: {current_node}")
            
            slot_output = {
                "value": node_result[slot]
            }
            output_data[slot] = slot_output 
            self._output_cache[slot] = slot_output

        return (output_data, current_node)

    def continue_process(self, scene: NodeScene):
        self.waiting_for_continue = False
        self.on_scene_changed(scene)

    
    def validate_scene(self, node_scene: NodeScene):
        pass


    def on_scene_changed(self, new_scene: NodeScene):
        # TODO: Actually check if the order is fine based on connections
        self._process_order = NodeUtils.get_node_execution_order(new_scene.nodes)
        
        self._output_cache = {}
        self._current_idx = 0
        self._previous_output = None
        if len(self._process_order) == 0:
            self._current_idx = None

    
# TODO: Use scene stuff from SceneManager to make actual Nodes from the Mirrors

class ServerInstance:
    _attributed_id: str = ""
    _runtime: BaseServerRuntime
    _on_output: Callable[[dict], None] | None = None

    running: bool = False
    auto_loop: bool = True
    
    mirror_manager: MirrorSceneManager
    _scene: NodeScene # TODO: talvez ser o SceneManager 

    def __init__(self, types: TypeFileReader | None = None):
        self.setup(types)

    def setup(self, types: TypeFileReader | None = None):
        self._runtime = BaseServerRuntime()
        self.mirror_manager = MirrorSceneManager(types)
        self._scene = NodeScene([], self.mirror_manager)


    def runtime_tick(self):
        if not self.running:
            return

        # FIXME
        if not self.mirror_manager.has_loaded_scene():
            return

        # TODO: Check if it should actually continue
        if self._runtime.waiting_for_continue and self.auto_loop:
            self._runtime.continue_process(self._scene)

        results = self._runtime.process_next(self._scene)
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


    def _scene_changed(self):
        self._runtime.on_scene_changed(self._scene) # FIXME

    def load_types(self, json_data: dict):
        self.mirror_manager.load_types(json_data)
        self._scene.update_nodes()

    def load_new_scene(self, json_data: dict):
        self.mirror_manager.load_new_scene(json_data)
        self._scene.update_nodes()


    def save_state(self):
        pass

    def load_state(self, something):
        pass