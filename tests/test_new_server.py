from pathlib import Path
from nodeserver.server.web.server import NodeServer

if __name__ == "__main__":
    tests_folder = Path(__file__).parent
    plugins_folder = tests_folder.parent / "test_plugins"
    scenes_folder = tests_folder.parent / "scenes"

    scenes_folder.mkdir(exist_ok=True)
    server = NodeServer(
        plugins_folder=plugins_folder,
        scenes_folder=scenes_folder,
    )
    server.run()
