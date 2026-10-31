from pathlib import Path

from pydantic_settings import BaseSettings


class EngineEnv(BaseSettings):
    core_plugins_folder: Path = Path(__file__).parent.parent.parent / "core_plugins"

    core_plugins: list[str] = ["core"]

ENGINE_ENV = EngineEnv()
