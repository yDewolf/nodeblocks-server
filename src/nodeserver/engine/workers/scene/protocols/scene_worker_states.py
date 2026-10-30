from enum import StrEnum


class SceneWorkerExecutionState(StrEnum):
    STOPPED = "stopped"
    RUNNING = "running"
    RUNNING_CONTINUOUS = "continuous"
    # FIXME Talvez ao invés de ter o running continuous, a gente usa o próprio
    # target iterations para lidar com isso


class SceneWorkerExecutionMode(StrEnum):
    FULL_GRAPH = "full_graph"
    GRAPH_STEP = "graph_step"

