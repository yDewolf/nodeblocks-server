import logging
from pathlib import Path

import platformdirs
from pydantic_settings import BaseSettings
from importlib import resources

nodeblocks_folder = Path(__file__).parent.parent
core_plugins_folder = nodeblocks_folder / "core_plugins"

with resources.path("nodeblocks", "core_plugins") as path:
    core_plugins_folder = path

class EngineEnv(BaseSettings):
    core_plugins_folder: Path = core_plugins_folder
    plugin_libs_folder: Path = platformdirs.user_data_path("nodeblocks")

    core_plugins: list[str] = ["core"]
    logging_level: int = logging.DEBUG

ENGINE_ENV = EngineEnv()
