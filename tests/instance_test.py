from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.server_instance import ServerInstance

manager = InstanceManager()

my_instance = ServerInstance()
manager.set_instance(
    "someRandomString", my_instance
)