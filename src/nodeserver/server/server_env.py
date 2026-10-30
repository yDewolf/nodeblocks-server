from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).parent.parent.parent.parent / ".env"
class ServerEnv(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")
    
    scene_autosave_interval: float = 3 * 60 # seconds

    secret_key: str = "missing"

    inactivty_check_interval: float = 15.0 # seconds
    scene_worker_grace_period: float = 5 * 60 # seconds
    worker_status_check_interval: float = 10.0 # seconds

SERVER_ENV = ServerEnv()
