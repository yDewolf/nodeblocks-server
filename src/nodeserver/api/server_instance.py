
import logging
import queue
from typing import Callable
from nodeserver.api.base_nodes import BaseNode
from nodeserver.api.instance_states import InstanceCommands, InstanceStates, LoopStates, StateController
from nodeserver.api.node_scene import NodeScene
from nodeserver.networking.nodes.data.node_data_types import SuperSlotTypes
from nodeserver.networking.nodes.helpers.file.typing_file_reader import TypeFileReader
from nodeserver.networking.nodes.helpers.scene_manager import MirrorSceneManager
from nodeserver.networking.nodes.node.base_nodes import NodeMirror, SlotMirror
from nodeserver.networking.nodes.node.node_utils import NodeUtils

INSTANCE_LOGGER = logging.Logger("InstanceLogger")

class BaseServerRuntime:
    _current_idx: int | None = None
    _process_order: list[NodeMirror] | None = None
    _output_cache: dict[SlotMirror, dict]

    _previous_output: dict | None = None
    waiting_to_continue: bool
    
    def __init__(self):
        self.waiting_to_continue = False

        
    def process_next(self, node_scene: NodeScene) -> tuple[dict[SlotMirror, dict] | None, BaseNode] | None:
        if self._current_idx == None or not self._process_order:
            return None
        
        if self._current_idx >= len(self._process_order):
            self.waiting_to_continue = True
            return None
        
        current_node = node_scene.get_node(self._process_order[self._current_idx].uid)
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
        self.waiting_to_continue = False
        self.on_scene_changed(scene)

    
    def validate_scene(self, node_scene: NodeScene):
        pass


    def on_scene_changed(self, new_scene: NodeScene):
        self._process_order = NodeUtils.get_node_execution_order(new_scene.nodes)
        
        self._output_cache = {}
        self._current_idx = 0
        self._previous_output = None
        if len(self._process_order) == 0:
            self._current_idx = None

    
class ServerInstance:
    _attributed_id: str = ""
    _runtime: BaseServerRuntime
    _on_output: Callable[[dict], None] | None = None

    state_controller: StateController

    mirror_manager: MirrorSceneManager
    _scene: NodeScene

    def __init__(self, types: TypeFileReader | None = None):
        self.setup(types)

    def setup(self, types: TypeFileReader | None = None):
        self.state_controller = StateController()
        self._runtime = BaseServerRuntime()
        self.mirror_manager = MirrorSceneManager(types)
        self._scene = NodeScene([], self.mirror_manager)


    def runtime_tick(self):
        if not self.is_running():
            return

        # FIXME
        if not self.mirror_manager.has_loaded_scene():
            return

        if self._runtime.waiting_to_continue:
            match self.state_controller.loop_state:
                case LoopStates.AUTO_LOOP:
                    self._runtime.continue_process(self._scene)
                
                case _:
                    # Any other will wait for resume commands
                    return

        if self.state_controller.loop_state == LoopStates.WAIT_TO_STEP:
            if not self.state_controller.has_step_permission:
                return

            self.state_controller.has_step_permission = False

        results = self._runtime.process_next(self._scene)
        if results != None and self._on_output != None:
            slot_results, node = results
            result_data = {}
            if slot_results != None:
                for slot, result in slot_results.items():
                    result_data[slot.slot_name] = result

            self._on_output({
                "type": "node_output",
                "node_id": node._mirror.uid,
                "value": result_data
            })
            
        INSTANCE_LOGGER.info("DEBUG: Running server instance")

    def _handle_command_queue(self):
        while not self.state_controller.command_queue.empty():
            try:
                command = self.state_controller.command_queue.get_nowait()
                self._handle_command(command)
            except queue.Empty:
                break

    def _handle_command(self, command: InstanceCommands):
        match command:
            case InstanceCommands.RUN:
                self.start_running()

            case InstanceCommands.STOP:
                self.stop_running()
            
            case InstanceCommands.RESUME_LOOP:
                if self.state_controller.loop_state != LoopStates.WAIT_TO_RESUME:
                    return
                
                if self._runtime.waiting_to_continue:
                    self._runtime.continue_process(self._scene)

            case InstanceCommands.STEP_NEXT:
                if self.state_controller.loop_state != LoopStates.WAIT_TO_STEP:
                    return
                
                if self._runtime.waiting_to_continue:
                    self._runtime.continue_process(self._scene)
                
                self.state_controller.has_step_permission = True

    def set_output_callback(self, callback: Callable[[dict], None]):
        self._on_output = callback


    def start_running(self):
        self.state_controller.queue_state(InstanceStates.RUNNING)

    def stop_running(self):
        self.state_controller.queue_state(InstanceStates.WAITING)

    def is_running(self):
        return self.state_controller.instance_state == InstanceStates.RUNNING


    def _scene_changed(self):
        self._runtime.on_scene_changed(self._scene) # FIXME

    def load_types(self, json_data: dict):
        self.mirror_manager.load_types(json_data)
        self._scene.update_nodes()

    def load_new_scene(self, json_data: dict):
        self.mirror_manager.load_new_scene(json_data)
        self._scene.update_nodes()
        self._scene_changed()


    def save_state(self):
        pass

    def load_state(self, something):
        pass