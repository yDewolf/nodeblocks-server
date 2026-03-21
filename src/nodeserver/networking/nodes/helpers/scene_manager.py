
from nodeserver.networking.nodes.helpers.connection_manager import ConnectionManager
from nodeserver.networking.nodes.helpers.file.node_scene_reader import SceneFileReader
from nodeserver.networking.nodes.helpers.file.typing_file_reader import TypeFileReader
from nodeserver.networking.nodes.helpers.node_manager import NodeManager


class SceneManager:
    type_reader: TypeFileReader
    scene_reader: SceneFileReader

    node_manager: NodeManager
    connection_manager: ConnectionManager

    def __init__(self) -> None:
        self.type_reader = TypeFileReader()
        self.scene_reader = SceneFileReader()
        self.node_manager = NodeManager()
        self.connection_manager = ConnectionManager()

    def clear_scene(self):
        self.node_manager.clear()
        self.connection_manager.clear()

    def load_types(self, json_data: dict):
        self.type_reader._load_json_data(json_data)

    def load_new_scene(self, json_data: dict):
        self.scene_reader._load_json_data(json_data)
        self.safe_parse_loaded_scene()

    def safe_parse_loaded_scene(self) -> bool:
        if not self.validate_loading_scene():
            return False

        self.scene_reader.swap_virtual_data()
        self.clear_scene()
        self._parse_loaded_node_scene()
        return True


    def validate_loading_scene(self) -> bool:
        if not self.scene_reader._virtual_file:
            return False

        if not self.scene_reader.is_virtual_data_compatible():
            return False
        
        if self.scene_reader._virtual_file.scene_data:
            if not self.type_reader.is_scene_compatible(self.scene_reader._virtual_file.scene_data):
                return False

        return True


    def _parse_loaded_node_scene(self) -> bool:
        if self.scene_reader.scene_data == None:
            return False
        
        for node_name, node_data in self.scene_reader.scene_data.nodes.items():
            constructor = self.type_reader.get_constructor(node_data.type)
            if node_data.id == -1:
                return False
            
            if constructor:
                new_node = constructor.make_node_mirror(
                    node_name,
                    node_data.id
                )
                if not new_node:
                    return False
                
                self.node_manager.add_node(new_node)

        for conn_data in self.scene_reader.scene_data.connections.values():
            if not conn_data.from_node.slot_name or not conn_data.to_node.slot_name:
                return False
            
            node_a = self.node_manager.get_node(conn_data.from_node.node_id)
            node_b = self.node_manager.get_node(conn_data.to_node.node_id)
            if not node_a or not node_b:
                return False

            slot_a = node_a.get_slot(conn_data.from_node.slot_name)
            slot_b = node_b.get_slot(conn_data.to_node.slot_name)
            if not slot_a or not slot_b:
                return False

            self.connection_manager.connect_nodes(slot_a, slot_b)

        return True

    
    def has_loaded_scene(self) -> bool:
        return self.scene_reader.scene_data != None