import logging
import queue
from typing import Any, Callable, Optional

from pydantic import BaseModel
from nodeserver.api.instance.actions.action_controller import Action, ActionController
from nodeserver.api.instance.actions.conn_actions import ConnActionUtils
from nodeserver.api.instance.actions.node_actions import NodeActionUtils
from nodeserver.api.instance.instance_states import InstanceCommands, InstanceStates, LoopStates, StateController
from nodeserver.api.internal.instance_state import InstanceState, InternalNodeState, InternalState, StateFileUtils
from nodeserver.api.internal.internal_protocols import InstanceProtocol
from nodeserver.api.node.nodes import _Node
from nodeserver.api.node.slots import _SlotIO
from nodeserver.api.web.requests.notification_requests import NotificationLevel, ServerNotification
from nodeserver.api.web.requests.request_unions import AnyServerMessage
from nodeserver.api.web.requests.websocket_requests import SrvNodeOutput, SrvSyncAction, SrvSyncState, SyncStatePayload
from nodeserver.api.web.websocket_protocol import ClientMessages, EditorActionStatus
from nodeserver.api.instance.node_scene import NodeScene
from nodeserver.wrapper.nodes.data.node_data_types import SuperSlotTypes
from nodeserver.wrapper.nodes.helpers.file.node_scene_dataclasses import SceneData
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import TypeFileReader
from nodeserver.wrapper.nodes.helpers.scene_manager import MirrorSceneManager
from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror, SlotMirror
from nodeserver.wrapper.nodes.node.node_utils import NodeUtils

logger = logging.getLogger("nds.instances")

class BaseServerRuntime:
    _current_idx: int | None = None
    _process_order: list[NodeMirror] | None = None
    _output_cache: dict[SlotMirror, _SlotIO]
    _node_execution_cache: dict[str, int]

    _previous_output: dict | None = None
    waiting_to_continue: bool
    
    def __init__(self):
        self.waiting_to_continue = False
        self._output_cache = {}
        self._node_execution_cache = {}

        
    def process_next(self, node_scene: NodeScene, instance_protocol: InstanceProtocol) -> Optional[tuple[dict[SlotMirror, _SlotIO] | None, _Node, bool]]:
        current_node = self._get_current_node(node_scene)
        if not current_node or self._current_idx == None: return
        self._current_idx += 1
        
        current_node._ensure_parameters_updated()

        current_hash = current_node.get_execution_hash(self._output_cache)
        last_hash = self._node_execution_cache.get(current_node._mirror.uid)
        if current_hash == last_hash and not current_node.bypass_cache:
            return (self._get_cached_outputs(current_node), current_node, True)

        try:
            raw_node_inputs = current_node.resolve_inputs(self._output_cache)
            node_inputs = current_node._parse_inputs(raw_node_inputs)
            current_node.pre_forward(node_inputs) # Node might set bypass cache to True here
            
            node_output: BaseModel = current_node.forward(node_inputs)
            output_model: dict = node_output.model_dump()
            output_data = self._update_outputs(current_node, output_model)

            current_node.post_forward()
            self._node_execution_cache[current_node._mirror.uid] = current_hash
            return (output_data, current_node, False)

        except Exception as e:
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
        self._process_order = NodeUtils.get_node_execution_order(new_scene.nodes)
        
        # self._output_cache = {}
        self._current_idx = 0
        self._previous_output = None
        if len(self._process_order) == 0:
            self._current_idx = None

    def reset_cache(self):
        self._node_execution_cache.clear()
        self._output_cache.clear()

    def _get_current_node(self, scene: NodeScene) -> Optional[_Node]:
        if self._current_idx == None or not self._process_order:
            return None
        
        if self._current_idx >= len(self._process_order):
            self.waiting_to_continue = True
            return None
        
        current_node = scene.get_node(self._process_order[self._current_idx].uid)
        if not isinstance(current_node, _Node):
            raise Exception(f"Node {current_node} doesn't extend {_Node}")
        
        if current_node == None:
            return None
    
        return current_node

    def _update_outputs(self, node: _Node, outputs: dict) -> dict[SlotMirror, _SlotIO]:
        output_data: dict[SlotMirror, _SlotIO] = {}
        for slot_name in outputs:
            slot = node.slot(slot_name)
            if slot._mirror.type._super_type != SuperSlotTypes.OUTPUT:
                logger.error(f"ERROR: Outputs should always come from an Output slot | Slot: {slot} | Node: {node}")
            
            slot._io.value = outputs[slot_name]
            output_data[slot._mirror] = slot._io
            self._output_cache[slot._mirror] = slot._io

        return output_data

    def _get_cached_outputs(self, node: _Node) -> dict[SlotMirror, _SlotIO]:
        return {
            slot: self._output_cache[slot]
            for slot in node._mirror.slots.get(SuperSlotTypes.OUTPUT, [])
            if slot in self._output_cache
        }


INSTANCE_VERSION: str = "0.3.1" # TODO: Use Version Manager
class ServerInstance:
    _attributed_id: str = ""
    _user_id: str = ""
    _created_at: float = 0

    _runtime: BaseServerRuntime
    _send_callback: Callable[[AnyServerMessage], None] | None = None

    state_controller: StateController
    action_controller: ActionController

    mirror_manager: MirrorSceneManager
    _scene: NodeScene

    def __init__(self, types: TypeFileReader | None = None):
        self.setup(types)

    def setup(self, types: TypeFileReader | None = None):
        self.state_controller = StateController(self._state_changed)
        self.action_controller = ActionController()

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

        if self.state_controller.loop_state == LoopStates.WAIT_STEP:
            if not self.state_controller.has_step_permission:
                return

            self.state_controller.has_step_permission = False

        results = self._runtime.process_next(self._scene, self)
        if results != None:
            slot_results, node, came_from_cache = results
            result_data = self._prepare_to_send_output(node, slot_results)
            
            # if not came_from_cache:
            self.send_to_client(SrvNodeOutput(
                node_id=node._mirror.uid,
                value=result_data
            ))
        logger.info("DEBUG: Running server instance")


    # Command Stuff
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
            
            case InstanceCommands.RESUME:
                if self.state_controller.loop_state != LoopStates.WAIT_RESUME:
                    return
                
                if self._runtime.waiting_to_continue:
                    self._runtime.continue_process(self._scene)

            case InstanceCommands.STEP:
                if self.state_controller.loop_state != LoopStates.WAIT_STEP:
                    return
                
                if self._runtime.waiting_to_continue:
                    self._runtime.continue_process(self._scene)
                
                self.state_controller.has_step_permission = True

    # Action Stuff
    def _handle_action_queue(self) -> dict[str, EditorActionStatus]:
        action_statuses: dict[str, EditorActionStatus] = {}
        while not self.action_controller.action_queue.empty():
            try:
                action = self.action_controller.action_queue.get_nowait()
                action_statuses[action.uid] = self._handle_action(action)
            
            except queue.Empty:
                break
            
        if action_statuses != {}:
            self.send_to_client(SrvSyncAction(
                action_statuses={
                    uid: status for uid, status in action_statuses.items()
                }
            ))
            self._scene_changed()
        
        return action_statuses

    def _handle_action(self, action: Action) -> EditorActionStatus:
        match action.target_type:
            case ClientMessages.NODE_ACTION:
                status = NodeActionUtils._parse_node_action(action, self)

            case ClientMessages.CONNECTION_ACTION:
                status = ConnActionUtils._parse_conn_action(action, self)

        return status

    def set_send_callback(self, callback: Callable[[AnyServerMessage], None]):
        self._send_callback = callback

    def send_to_client(self, message: AnyServerMessage):
        if self._send_callback:
            self._send_callback(message)

    def _prepare_to_send_output(self, node: _Node, slot_results: dict[SlotMirror, _SlotIO] | None):
        result_data = {}
        if slot_results != None:
            for slot, result in slot_results.items():
                result_data[slot.slot_name] = result.value
        
        return result_data


    def start_running(self):
        self.state_controller.queue_state(InstanceStates.RUNNING)

    def stop_running(self):
        self.state_controller.queue_state(InstanceStates.WAITING)

    def is_running(self) -> bool:
        return self.state_controller.instance_state == InstanceStates.RUNNING

    def is_waiting(self) -> bool:
        if self.state_controller.instance_state == InstanceStates.WAITING:
            return True
        
        if self.state_controller.instance_state == InstanceStates.RUNNING:
            if self._runtime.waiting_to_continue and self.state_controller.loop_state == LoopStates.WAIT_RESUME:
                return True
            
        return False


    def _scene_changed(self):
        self._runtime.on_scene_changed(self._scene) # FIXME

    def load_types(self, json_data: dict):
        self.mirror_manager.load_types(json_data)
        self._scene.update_nodes()

    def load_new_scene(self, json_data: dict| SceneData):
        self.mirror_manager.load_new_scene(json_data)
        self._scene.update_nodes()
        self._scene_changed()


    def _state_changed(self):
        self.send_to_client(SrvSyncState(
            payload=SyncStatePayload(
                loop_state=self.state_controller.loop_state,
                instance_state=self.state_controller.instance_state
            )
        ))
        # FIXME: Testing notifications:
        self.send_to_client(ServerNotification.notify(
            message="State changed!",
            level=NotificationLevel.DEBUG
        ))


    def save_internal_state(self, instance_path: str, node_state_path: str) -> Optional[InstanceState]:
        scene_data = self.mirror_manager.get_scene()
        if not scene_data:
            return
        
        nodes_internal_state: dict[str, InternalNodeState] = {}
        for node in self._scene.nodes:
            internal_state = node.save_state(node_state_path)
            
            if internal_state:
                nodes_internal_state[node._mirror.uid] = internal_state

        state_data = InstanceState(
            instance_id=self._attributed_id,
            user_id=self._user_id,
            instance_creation_time=self._created_at,
            instance_version=INSTANCE_VERSION,
            scene_data=scene_data,
            types_data=self.mirror_manager.type_reader.serialize(),
            internal_states=InternalState(
                nodes=nodes_internal_state
            )
        )

        StateFileUtils.save_instance_state(state_data, instance_path)
        self.send_to_client(ServerNotification.notify(
            message="Instance saved.",
            level=NotificationLevel.INFO
        ))
        return state_data

    def load_internal_state(self, instance_path: str, node_state_path: str, state: InstanceState):
        # TODO: Check type stuff
        self.load_new_scene(state.scene_data)
        for node in self._scene.nodes:
            node_state = state.internal_states.nodes.get(node._mirror.uid)
            if node_state:
                node.load_state(node_state_path, node_state)

                self.send_to_client(ServerNotification.notify(
                    message="Loaded Internal State!",
                    level=NotificationLevel.INFO,
                ))
