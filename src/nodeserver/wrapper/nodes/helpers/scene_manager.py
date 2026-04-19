
from nodeserver.wrapper.nodes.helpers.connection_manager import ConnectionManager
from nodeserver.wrapper.nodes.helpers.file.node_scene_dataclasses import ConnectionSceneData, NodeSceneData, SceneData
from nodeserver.wrapper.nodes.helpers.file.node_scene_reader import SceneFileReader
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import TypeFileReader
from nodeserver.wrapper.nodes.helpers.node_manager import NodeMirrorManager
from nodeserver.wrapper.nodes.node.base_nodes import ConnectionMirror, NodeMirror

class MirrorSceneManager:
    type_reader: TypeFileReader
    scene_reader: SceneFileReader

    node_manager: NodeMirrorManager
    connection_manager: ConnectionManager

    def __init__(self, types: TypeFileReader | None = None) -> None:
        self.type_reader = types if types != None else TypeFileReader()
        self.scene_reader = SceneFileReader()
        self.node_manager = NodeMirrorManager()
        self.connection_manager = ConnectionManager()

        if self.type_reader._node_types_id and self.type_reader._node_types_version != -1:
            self.scene_reader.new_scene(self.type_reader._node_types_id, self.type_reader._node_types_version)

    def clear_scene(self):
        self.node_manager.clear()
        self.connection_manager.clear()

    def load_types(self, json_data: dict):
        self.type_reader._load_json_data(json_data)

    def load_new_scene(self, json_data: dict| SceneData):
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
            self.add_node_mirror(node_data, node_name, update_scene_data=False)

        for conn_data in self.scene_reader.scene_data.connections.values():
            self.add_conn_mirror(conn_data, update_scene_data=False)

        return True

    
    def has_loaded_scene(self) -> bool:
        return self.scene_reader.scene_data != None


    def add_node_mirror(self, node_data: NodeSceneData, node_name: str, update_scene_data: bool = True) -> NodeMirror | None:
        constructor = self.type_reader.get_constructor(node_data.type)
        if node_data.uid == None or not constructor:
            return None
        
        new_mirror = constructor.make_node_mirror(
            node_name,
            node_data.uid,
            node_data.data,
            node_data.position.serialize()
        )

        if not new_mirror:
            return None
        
        if update_scene_data and self.scene_reader.scene_data and new_mirror:
            self.scene_reader.scene_data.nodes[new_mirror.uid] = node_data

        self.node_manager.add_node(new_mirror)
        return new_mirror

    def add_conn_mirror(self, conn_data: ConnectionSceneData, update_scene_data: bool = True) -> ConnectionMirror | None:
        if not conn_data.from_slot.slot_name or not conn_data.to_slot.slot_name:
            return None
        
        node_a = self.node_manager.get_node(conn_data.from_slot.node_id)
        node_b = self.node_manager.get_node(conn_data.to_slot.node_id)
        if not node_a or not node_b:
            return None

        slot_a = node_a.get_slot(conn_data.from_slot.slot_name)
        slot_b = node_b.get_slot(conn_data.to_slot.slot_name)
        if not slot_a or not slot_b:
            return None

        conn = self.connection_manager.connect_nodes(slot_a, slot_b, conn_data.uid)
        if update_scene_data and self.scene_reader.scene_data and conn:
            self.scene_reader.scene_data.connections[conn.uid] = conn_data
        
        return conn


    def remove_node_mirrors(self, uids: list[str], update_scene_data: bool = True):
        results: list[bool] = []
        for uid in uids:
            if update_scene_data and self.scene_reader.scene_data:
                self.scene_reader.scene_data.nodes.pop(uid)

            results.append(self.node_manager.remove_node(uid))
        
        return results

    def remove_conn_mirror(self, uids: list[str], update_scene_data: bool = True):
        results: list[bool] = []
        for uid in uids:
            if update_scene_data and self.scene_reader.scene_data:
                self.scene_reader.scene_data.connections.pop(uid)

            results.append(self.connection_manager.remove_connection(uid))

        return results
    

    def get_scene_as_dict(self) -> dict:
        return self.scene_reader.scene_data.serialize() if self.scene_reader.scene_data else {}