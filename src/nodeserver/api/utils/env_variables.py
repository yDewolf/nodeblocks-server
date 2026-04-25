import os
from dotenv import load_dotenv

from nodeserver.api.utils.file_utils import get_project_root

load_dotenv()

secret_key = os.getenv("SECRET_KEY")
SECRET_KEY = secret_key if secret_key else ""
if SECRET_KEY == "":
    print("WARNING: You need to set a SECRET_KEY on .env file")

grace_period = os.getenv("SESSION_GRACE_PERIOD")
SESSION_GRACE_PERIOD: int = int(grace_period) if grace_period != None else 120

state_path = os.getenv("INSTANCE_STATE_PATH")
WORKSPACES_PATH: str = state_path if state_path else str(get_project_root()) + "/_workspaces"

