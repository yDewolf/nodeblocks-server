from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.server_instance import ServerInstance
from logging import Logger

manager = InstanceManager()

my_instance = ServerInstance()
result = manager.set_instance(
    "someRandomString", my_instance
)
print(result)

logger = Logger("logger")

my_instance.start_running()
while True:
    pass