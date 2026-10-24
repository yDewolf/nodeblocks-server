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
    SAVE_SCENE = "save_scene"
    SET_SCENE_AUTOSAVE = "set_scene_autosave" # TODO: talvez isso deveria ser outro tipo de comando
    GET_SCENE_DATA = "get_scene_data"

# TODO: fazer esse set scene autosave se tornar um 
# comando de configuração geral da cena com outras opções

# -- Scene Execution 

class SceneExecutionCmdTypes(StrEnum):
    CHECK_EXECUTION_STATE = "check_execution_state"
    SET_EXECUTION_STATE = "set_execution_state"
    SET_EXECUTION_MODE = "set_execution_mode"
    EXECUTION_SHORTCUT = "execution_shortcut"
    UPDATE_TARGET_NODES = "update_target_nodes"
    UPDATE_EXECUTION_CONFIG = "update_execution_config"

# TODO repensar o nome desse enum
# 
class ExecutionShortcuts(StrEnum):
    EXECUTION_STEP = "step"
    EXECUTION_PAUSE = "pause"
    EXECUTION_CONTINUE = "continue" # resume
