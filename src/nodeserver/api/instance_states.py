from enum import Enum
import queue

class InstanceStates(Enum):
    WAITING = 0
    RUNNING = 1

class LoopStates(Enum):
    AUTO_LOOP = 0 # Keeps the loop running
    WAIT_TO_RESUME = 1 # Runs the full loop and waits
    WAIT_TO_STEP = 2 # Process a node and waits

class InstanceCommands(Enum):
    STEP_NEXT = 0
    RESUME_LOOP = 1
    STOP = 2
    RUN = 3

class StateController:
    state_queue: queue.Queue[tuple[str, InstanceStates | LoopStates]]
    command_queue: queue.Queue[InstanceCommands]

    instance_state: InstanceStates
    loop_state: LoopStates

    has_step_permission: bool

    def __init__(self) -> None:
        self.has_step_permission = False
        self.state_queue = queue.Queue()
        self.command_queue = queue.Queue()

        self.instance_state = InstanceStates.WAITING
        self.loop_state = LoopStates.AUTO_LOOP    

    def queue_command(self, command: InstanceCommands):
        self.command_queue.put(command)

    def queue_state(self, new_state: InstanceStates):
        self.state_queue.put(("SET_INSTANCE_STATE", new_state))

    def queue_loop_state(self, new_state: LoopStates):
        self.state_queue.put(("SET_LOOP_STATE", new_state))
    

    def update(self):
        while not self.state_queue.empty():
            command, state = self.state_queue.get_nowait()
            match command:
                case "SET_INSTANCE_STATE": 
                    print(f"Instance State: {state}")
                    self.instance_state = state # type: ignore
                
                case "SET_LOOP_STATE": 
                    print(f"Loop State: {state}")
                    self.loop_state = state # type: ignore
