import os
from dotenv import find_dotenv, load_dotenv, set_key

from nodeserver.api.utils.file_utils import FileUtils

dotenv_path = find_dotenv(raise_error_if_not_found=True)
load_dotenv(dotenv_path)

def get_project_root():
    if not FileUtils._project_root:
        project_root_path = os.getenv("PROJECT_ROOT_PATH")
        if project_root_path: 
            FileUtils.set_project_root(project_root_path)
        else:
            FileUtils.select_project_root()

    return str(FileUtils._project_root)

secret_key = os.getenv("SECRET_KEY")
SECRET_KEY = secret_key if secret_key else ""
if SECRET_KEY == "":
    print("WARNING: You need to set a SECRET_KEY on .env file")

#  In seconds:
grace_period = os.getenv("SESSION_GRACE_PERIOD")
SESSION_GRACE_PERIOD: int = int(grace_period) if grace_period != None else 120

state_path = os.getenv("INSTANCE_STATE_PATH")
WORKSPACES_PATH: str = state_path if state_path else str(get_project_root()) + "/_workspaces"

#  In minutes:
instance_autosave_interval = os.getenv("INSTANCE_AUTOSAVE_INTERVAL")
INSTANCE_AUTOSAVE_INTERVAL: int = int(instance_autosave_interval) if instance_autosave_interval else 3
