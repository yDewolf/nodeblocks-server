
from nodeserver.api.base_nodes import BaseNode


class NodeScene:
    nodes: list[BaseNode]
    # connections: list[NodeConnection]
    
    def __init__(self, nodes: list[BaseNode]) -> None:
        self.nodes = nodes
    
    
    
    # TODO: Scene Updates
    
    
    def get_node(self, node_id: int) -> BaseNode | None:
        for node in self.nodes:
            if node._mirror.id == node_id:
                return node
            
        return None
    
    def add_node(self, node: BaseNode):
        if self.nodes.__contains__(node):
            return
        
        self.nodes.append(node)