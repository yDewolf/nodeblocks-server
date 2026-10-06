from enum import StrEnum


# -- Graph

class GraphActionTypes(StrEnum):
    ADD = "add"
    REMOVE = "remove"
    UPDATE = "update"

class ClientGraphCommandTypes(StrEnum):
    NODE = "node"
    CONN = "conn"

# -- Scene Commands

class ClientSceneCommandTypes(StrEnum):
    LOAD_SCENE = "load_scene"

# -- Scene Execution 

class SceneExecutionCmdTypes(StrEnum):
    SET_EXECUTION_STATE = "set_execution_state"
    SET_EXECUTION_MODE = "set_execution_mode"
    EXECUTION_SHORTCUT = "execution_shortcut"
    # TODO: update target nodes

# TODO repensar o nome desse enum
# 
class ExecutionShortcuts(StrEnum):
    EXECUTION_STEP = "step"
    EXECUTION_PAUSE = "pause"
    EXECUTION_CONTINUE = "continue" # resume
