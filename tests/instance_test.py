from logging import Logger

from nodeserver.api.base_nodes import BaseNode
from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.node_scene import NodeScene
from nodeserver.api.server_instance import ServerInstance
from nodeserver.networking.nodes.data.node_data import NodeData
from nodeserver.networking.nodes.data.slot_data import SlotData
from nodeserver.networking.nodes.node.base_nodes import NodeMirror
from nodeserver.networking.nodes.node_constructor import CustomNodeConstructor

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

constructor = CustomNodeConstructor(
    "SomeType", NodeData({}), 
    {"in_0": SlotData("input_slot", "float"), "out_0": SlotData("output_slot", "float")}, 
    {}
)
nodes: list = []
for i in range(5):
    mirror = constructor.make_node_mirror(
        "TestNode", i
    )
    if mirror:
        nodes.append(MyCustomNode.from_mirror(mirror))

my_instance._scene_changed(NodeScene(
    nodes
))

while True:
    pass