import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

grace_period = os.getenv("SESSION_GRACE_PERIOD")
SESSION_GRACE_PERIOD = int(grace_period) if grace_period != None else 120