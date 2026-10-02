
from pathlib import Path

from nodeserver.engine.workers.protocols.scene_worker_commands import UpdateExecutionStateCmd, GraphExecutionModes, LoadSceneCommand
from nodeserver.engine.workers.protocols.scene_worker_protocol import EvtWorkerReady
from nodeserver.protocols.manifest.node.node_graph import SceneData
from nodeserver.server.workers.scene_worker_controller import SceneWorkerController
import logging.config

logging.config.fileConfig("logging.conf")

if __name__ == "__main__":
    plugins_folder = Path(__file__).parent.parent.parent / "test_plugins"
    controller = SceneWorkerController("test_0", plugins_folder)

    controller.start()
    is_ready = False
    while not is_ready:
        events = controller.get_events()
        for event in events:
            if isinstance(event, EvtWorkerReady):
                is_ready = True
                break

    controller.send_command(LoadSceneCommand(
        scene_data=SceneData(
            package_id="core", package_version="0.0.0"
        )
    ))
    controller.send_command(
        UpdateExecutionStateCmd(
            state=GraphExecutionModes.CONTINUOUS
        )
    )
    input("Press enter to quit")
    events = controller.get_events()
    print(events)
    controller.stop()
