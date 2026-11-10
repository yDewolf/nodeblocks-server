from pathlib import Path

import platformdirs
from pydantic_settings import BaseSettings


src_folder = Path(__file__).parent.parent.parent
class EngineEnv(BaseSettings):
    core_plugins_folder: Path = src_folder / "core_plugins"
    plugin_libs_folder: Path = platformdirs.user_data_path("nodeblocks")

    core_plugins: list[str] = ["core"]

ENGINE_ENV = EngineEnv()
