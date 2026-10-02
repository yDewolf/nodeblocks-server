from pathlib import Path
from nodeserver.server.web.server import NodeServer

if __name__ == "__main__":
    tests_folder = Path(__file__).parent

    server = NodeServer(
        plugins_folder=tests_folder.parent / "test_plugins",
        scenes_folder=tests_folder.parent / "scenes",
    )
    server.run()
