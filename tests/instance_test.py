from nodeserver.api.base_nodes import BaseNode
from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.node_scene import NodeScene
from nodeserver.api.server_instance import ServerInstance
from logging import Logger

from nodeserver.networking.nodes.data.node_data import NodeData
from nodeserver.networking.nodes.node.base_nodes import NodeMirror

manager = InstanceManager()

my_instance = ServerInstance()
result = manager.set_instance(
    "someRandomString", my_instance
)
print(result)

logger = Logger("logger")

my_instance.start_running()

nodes: list[BaseNode] = []
for i in range(5):
    new_node = BaseNode.from_mirror(
        NodeMirror(
            "BaseNode",
            NodeData({}),
            i,
        )
    )
    nodes.append(new_node)

my_instance._scene_changed(NodeScene(
    nodes
))

while True:
    pass