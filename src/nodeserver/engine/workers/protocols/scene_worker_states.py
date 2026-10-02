from enum import StrEnum


class SceneWorkerExecutionState(StrEnum):
    STOPPED = "stopped"
    RUNNING = "running"
    RUNNING_CONTINUOUS = "continuous"


class SceneWorkerExecutionMode(StrEnum):
    FULL_GRAPH = "full_graph"
    GRAPH_STEP = "graph_step"

