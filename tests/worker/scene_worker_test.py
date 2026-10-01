
from pathlib import Path

from nodeserver.engine.workers.protocols.scene_worker_commands import ExecuteGraphCommand, GraphExecutionModes
from nodeserver.engine.workers.protocols.scene_worker_protocol import EvtWorkerReady
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

    controller.send_command(
        ExecuteGraphCommand(
            mode=GraphExecutionModes.FULL_GRAPH
        )
    )
    input("Press enter to quit")
    controller.stop()
