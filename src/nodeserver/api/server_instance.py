
from logging import Logger

from nodeserver.api.base_nodes import BaseNode

# TODO: make a node_scene class with every node and connections + other things related to the scene
INSTANCE_LOGGER = Logger("InstanceLogger")

class BaseServerRuntime:
    def __init__(self):
        pass

    def forward_nodes(self, node_scene: list[BaseNode]):
        pass

    
    def validate_scene(self, node_scene: list[BaseNode]):
        pass


# TODO:
class ServerInstance:
    _attributed_id: str = ""

    _runtime: BaseServerRuntime
    running: bool = False
    
    nodes: list[BaseNode] = []

    def __init__(self):
        self.setup()

    def setup(self):
        self._runtime = BaseServerRuntime()


    def running_loop(self):
        if not self.running:
            return

        self._runtime.forward_nodes(self.nodes)
        INSTANCE_LOGGER.debug("DEBUG: Running server instance")
        

    def start_running(self):
        self.running = True

    def stop_running(self):
        self.running = False


    
    def add_node(self, node: BaseNode):
        if self.nodes.__contains__(node):
            return
        
        self.nodes.append(node)


    def save_state(self):
        pass

    def load_state(self, something):
        pass