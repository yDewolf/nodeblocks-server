
from typing import Optional

from nodeserver.engine.protocols.graph.connection_manager import ConnectionManager
from nodeserver.engine.protocols.graph.node_manager import NodeManager
from nodeserver.engine.protocols.node_instance import SlotInstance
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.manifest.node.node_graph import ConnectionSceneData


class SceneGraph:
    type_registry: TypeRegistry

    nodes: NodeManager
    connections: ConnectionManager

    def __init__(self, registry: TypeRegistry):
        self.registry = registry

        self.nodes = NodeManager()
        self.connections = ConnectionManager(registry)

    def connect_slots(self, from_slot: SlotInstance, to_slot: SlotInstance) -> Optional[ConnectionSceneData]:
        conn = self.connections.connect_slots(from_slot, to_slot)
        return conn

    def connect(self, from_node_id: str, from_slot_id: str, to_node_id: str, to_slot_id: str) -> Optional[ConnectionSceneData]:
        from_node = self.nodes.get(from_node_id)
        to_node = self.nodes.get(to_node_id)

        if not from_node or not to_node:
            return None

        from_slot = from_node.slots.get(from_slot_id)
        to_slot = to_node.slots.get(to_slot_id)

        if not from_slot or not to_slot:
            return None

        return self.connect_slots(from_slot, to_slot)

    def disconnect(self, conn_id: str):
        conn = self.connections.remove(conn_id)
        if not conn:
            return

        from_node = self.nodes.get(conn.from_slot.node_id)
        to_node = self.nodes.get(conn.to_slot.node_id)
        if not from_node or not to_node:
            return

        from_slot = from_node.slots.get(conn.from_slot.slot_id)
        to_slot = to_node.slots.get(conn.to_slot.slot_id)
        if from_slot:
            from_slot.connection_count = max(0, from_slot.connection_count - 1)
        
        if to_slot:
            to_slot.connection_count = max(0, to_slot.connection_count - 1)


    def remove_node(self, node_id: str):
        node = self.nodes.remove(node_id)
        if not node:
            return

        attached_connections = self.connections.get_by_node(node_id)
        for conn in attached_connections:
            self.disconnect(conn.uid)
        
