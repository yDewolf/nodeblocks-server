from nodeserver.api.base_nodes import BaseNode
from nodeserver.api.node_builder import BaseNodeBuilder
from nodeserver.networking.nodes.helpers.scene_manager import MirrorSceneManager


# TODO: Fazer um parser dos mirrors, cada alteração nos mirrors precisa refletir na NodeScene

# Controla que nodes devem ser adicionados, atualizados, etc.
# Usa um Builder customizado para converter um NodeMirror em um BaseNode
class NodeScene:
    nodes: list[BaseNode] # Instâncias dos Mirrors
    mirror_manager: MirrorSceneManager
    _builder_class: type[BaseNodeBuilder]
    _builder: BaseNodeBuilder
    # connections: list[NodeConnection]
    
    def __init__(self, nodes: list[BaseNode], mirror_manager: MirrorSceneManager, builder_class: type[BaseNodeBuilder]) -> None:
        self._builder_class = builder_class

        self.nodes = nodes
        self.mirror_manager = mirror_manager
        self._builder = self._builder_class()

    
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


    def update_nodes(self):
        self.nodes.clear() # FIXME
        for id, mirror in self.mirror_manager.node_manager._nodes.items():
            new_node = self._builder.build_node(mirror)
            self.nodes.append(new_node)