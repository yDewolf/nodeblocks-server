from nodeserver.api.base_nodes import BaseNode
from nodeserver.networking.nodes.helpers.scene_manager import MirrorSceneManager


# TODO: Fazer um parser dos mirrors, cada alteração nos mirrors precisa refletir na NodeScene

# Controla que nodes devem ser adicionados, atualizados, etc.
# Usa um Builder customizado para converter um NodeMirror em um BaseNode
class NodeScene:
    nodes: list[BaseNode] # Instâncias dos Mirrors
    mirror_manager: MirrorSceneManager
    # connections: list[NodeConnection]
    
    def __init__(self, nodes: list[BaseNode], mirror_manager: MirrorSceneManager) -> None:
        self.nodes = nodes
        self.mirror_manager = mirror_manager

    
    # TODO: Scene Updates
    
    
    def get_node(self, node_uid: str) -> BaseNode | None:
        for node in self.nodes:
            if node._mirror.uid == node_uid:
                return node
            
        return None
    
    def add_node(self, node: BaseNode):
        if self.nodes.__contains__(node):
            return
        
        self.nodes.append(node)


    def update_nodes(self) -> bool:
        self.nodes.clear() # FIXME
        for id, mirror in self.mirror_manager.node_manager._nodes.items():
            constructor = self.mirror_manager.type_reader.node_constructors.get(mirror.type_name)
            if not constructor:
                return False
        
            new_node = constructor.build_node(mirror)
            print(f"Parsed mirror to {new_node}")
            self.nodes.append(new_node)
        
        return True