from logging import Logger

from nodeserver.api.base_nodes import BaseNode
from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.server_instance import ServerInstance
from nodeserver.networking.nodes.node.base_nodes import NodeMirror
from test_data import SCENE_DATA_JSON, TYPE_FILE_JSON

LOGGER = Logger("logger")

class MyCustomNode(BaseNode):
    some_parameter: float = 1.0
    def __init__(self):
        super().__init__()

    @staticmethod
    def from_mirror(mirror: NodeMirror):
        new_node = MyCustomNode()
        new_node._mirror = mirror

        return new_node

    def forward(self, input):
        if type(input) is float or type(input) is int:
            LOGGER.info(f"Node {self} received input: {input}")
            return input + 1


manager = InstanceManager()

my_instance = ServerInstance()
result = manager.set_instance(
    "someRandomString", my_instance
)
print(f"Created instance? {result}")
my_instance.start_running()
my_instance.scene_manager.load_types(TYPE_FILE_JSON)
my_instance.scene_manager.load_new_scene(SCENE_DATA_JSON)

my_instance._scene_changed()

while True:
    pass