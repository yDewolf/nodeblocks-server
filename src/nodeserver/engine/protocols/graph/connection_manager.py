
from typing import Optional

from nodeserver.engine.exceptions.graph_exceptions import ConnectionValidationError, CyclicConnectionError, IncompatibleSlotsError, MaxConnectionReached
from nodeserver.engine.protocols.node.node_instance import SlotInstance
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.manifest.node.node_graph import ConnectionSceneData, NodePathData


class ConnectionManager:
    _connections: dict[str, ConnectionSceneData] = {}
    _registry: TypeRegistry

    @property
    def conn_index(self): return self._connections

    @property
    def connections(self): return self._connections.values()

    @property
    def conn_ids(self): return self._connections.keys()

    def __init__(self, type_registry: TypeRegistry) -> None:
        self._registry = type_registry
        self._connections = {}

    
    def connect_slots(self, from_slot: SlotInstance, to_slot: SlotInstance) -> Optional[ConnectionSceneData]:
        self.validate_connection(from_slot, to_slot)
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
            raise KeyError("Another connection with the same UID already exists")

        self._connections[connection.uid] = connection

    def remove(self, connection_uid: str) -> Optional[ConnectionSceneData]:
        return self._connections.pop(connection_uid, None)


    # Getters

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

    # Validation

    def validate_connection(self, from_slot: SlotInstance, to_slot: SlotInstance) -> None:
        if not to_slot.can_connect or not from_slot.can_connect:
            raise MaxConnectionReached("One of the slots already reached its max connections")

        are_compatible = self._registry.are_types_compatible(
            from_slot.data_type_id, to_slot.data_type_id
        )
        if not are_compatible:
            raise IncompatibleSlotsError(
                f"Incompatible types: {from_slot.data_type_id} -> {to_slot.data_type_id}"
            )

        from_node = from_slot.node_id
        to_node = to_slot.node_id
        if from_node == to_node:
            raise CyclicConnectionError()

        if self._has_path(start_node_id=to_node, target_node_id=from_node):
            raise CyclicConnectionError()

    def can_connect(self, from_slot: SlotInstance, to_slot: SlotInstance) -> bool:
        try:
            self.validate_connection(from_slot, to_slot)
            return True
        except ConnectionValidationError:
            return False

    # Topology Utils

    def _has_path(self, start_node_id: str, target_node_id: str) -> bool:
        if start_node_id == target_node_id:
            return True

        visited: set[str] = set()
        stack: list[str] = [start_node_id]

        while stack:
            current_id = stack.pop()
            if current_id == target_node_id:
                return True

            if current_id not in visited:
                visited.add(current_id)
                outgoing_nodes = self._get_downstream_node_ids(current_id)
                stack.extend(outgoing_nodes - visited)

        return False

    def _get_downstream_node_ids(self, node_id: str) -> set[str]:
        downstream: set[str] = set()
        for conn in self._connections.values():
            if conn.from_slot.node_id == node_id:
                downstream.add(conn.to_slot.node_id)
        
        return downstream
