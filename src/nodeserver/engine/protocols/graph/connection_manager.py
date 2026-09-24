
from typing import Optional

from nodeserver.engine.protocols.node_instance import SlotInstance
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.helpers.datatype_helper import DatatypeHelper
from nodeserver.protocols.manifest.node.node_graph import ConnectionSceneData, NodePathData


class ConnectionManager:
    _connections: dict[str, ConnectionSceneData] = {}
    _registry: TypeRegistry

    def __init__(self, type_registry: TypeRegistry) -> None:
        self._registry = type_registry
        self._connections = {}

    def can_connect(self, from_slot: SlotInstance, to_slot: SlotInstance):
        if not to_slot.can_connect or not from_slot.can_connect:
            return False

        return self._registry.are_types_compatible(from_slot.data_type_id, to_slot.data_type_id)

    def connect_slots(self, from_slot: SlotInstance, to_slot: SlotInstance) -> Optional[ConnectionSceneData]:
        if not self.can_connect(from_slot, to_slot):
            return None

        conn = ConnectionSceneData(
            from_slot=NodePathData(node_id=from_slot.node_id, slot_id=from_slot.slot_id),
            to_slot=NodePathData(node_id=to_slot.node_id, slot_id=to_slot.slot_id)
        )
        self.add(conn)

        from_slot.connection_count += 1
        to_slot.connection_count += 1

        return conn


    def add(self, connection: ConnectionSceneData) -> None:
        if connection.uid in self._connections:
            raise Exception("Another connection with the same UID already exists")

        self._connections[connection.uid] = connection

    def remove(self, connection_uid: str) -> Optional[ConnectionSceneData]:
        return self._connections.pop(connection_uid, None)

    def get(self, connection_uid: str) -> Optional[ConnectionSceneData]:
        return self._connections.get(connection_uid, None)

    def get_by_node(self, node_id: str) -> list[ConnectionSceneData]:
        # FIXME: talvez fazer um cache disso aqui
        return [
            conn for conn in self._connections.values()
            if conn.from_slot.node_id == node_id or conn.to_slot.node_id == node_id
        ]

    def all(self) -> dict[str, ConnectionSceneData]:
        return self._connections
