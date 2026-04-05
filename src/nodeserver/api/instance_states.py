from enum import Enum
import queue
import logging
from typing import Callable


logger = logging.getLogger("nds.instances")

class InstanceStates(Enum):
    WAITING = 0
    RUNNING = 1

class LoopStates(Enum):
    AUTO_LOOP = "auto_loop" # Keeps the loop running
    WAIT_RESUME = "wait_resume" # Runs the full loop and waits
    WAIT_STEP = "wait_step" # Process a node and waits

class InstanceCommands(Enum):
    STEP = "STEP"
    RESUME = "RESUME"
    STOP = "STOP"
    RUN = "RUN"

class StateController:
    state_queue: queue.Queue[tuple[str, InstanceStates | LoopStates]]
    command_queue: queue.Queue[InstanceCommands]

    instance_state: InstanceStates
    loop_state: LoopStates

    has_step_permission: bool
    _on_state_changed: Callable[[], None] | None

    def __init__(self, on_state_changed: Callable[[], None] | None = None) -> None:
        self._on_state_changed = on_state_changed

        self.has_step_permission = False
        self.state_queue = queue.Queue()
        self.command_queue = queue.Queue()

        self.instance_state = InstanceStates.WAITING
        self.loop_state = LoopStates.WAIT_STEP

    def queue_command(self, command: InstanceCommands):
        self.command_queue.put(command)

    def queue_state(self, new_state: InstanceStates):
        self.state_queue.put(("SET_INSTANCE_STATE", new_state))

    def queue_loop_state(self, new_state: LoopStates):
        self.state_queue.put(("SET_LOOP_STATE", new_state))
    

    def _set_instance_state(self, new_state: InstanceStates):
        if new_state != self.instance_state:
            self.instance_state = new_state
        
        if self._on_state_changed:
            self._on_state_changed()

    def _set_loop_state(self, new_state: LoopStates):
        if new_state != self.loop_state:
            self.loop_state = new_state

        if self._on_state_changed:
            self._on_state_changed()

    def update(self):
        while not self.state_queue.empty():
            command, state = self.state_queue.get_nowait()
            match command:
                case "SET_INSTANCE_STATE": 
                    logger.debug(f"Instance State: {state}")
                    self._set_instance_state(state) # type: ignore
                
                case "SET_LOOP_STATE": 
                    logger.debug(f"Loop State: {state}")
                    self._set_loop_state(state) # type: ignore

