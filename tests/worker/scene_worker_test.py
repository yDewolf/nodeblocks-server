import logging
from nodeserver.engine.logging_config import setup_logging

setup_logging(default_level=logging.DEBUG)

from pathlib import Path

from nodeserver.engine.workers.protocols.scene_worker_commands import UpdateExecutionStateCmd, LoadSceneCommand
from nodeserver.engine.workers.protocols.scene_worker_protocol import EvtWorkerReady
from nodeserver.engine.workers.protocols.scene_worker_states import SceneWorkerExecutionState
from nodeserver.protocols.manifest.node.node_graph import SceneData
from nodeserver.server.workers.scene_worker_controller import SceneWorkerController

if __name__ == "__main__":
    plugins_folder = Path(__file__).parent.parent.parent / "test_plugins"
    controller = SceneWorkerController("test_0", plugins_folder)

    controller.start(wait_ready=True)
    controller.send_command(LoadSceneCommand(
        scene_data=SceneData(
            dependencies={"core": "0.1.0"}
        )
    ))
    controller.send_command(
        UpdateExecutionStateCmd(
            state=SceneWorkerExecutionState.RUNNING_CONTINUOUS
        )
    )
    input("Press enter to quit")
    events = controller.get_events()
    print(events)
    controller.stop()
