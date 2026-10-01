
from collections import deque
from typing import Optional, Union, overload

from nodeserver.engine.exceptions.graph_exceptions import ConnectionValidationError, CyclicConnectionError, DuplicateConnectionError, IncompatibleSlotsError, MaxConnectionReached
from nodeserver.engine.protocols.node.node_instance import SlotInstance
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.manifest.node.node_graph import ConnectionSceneData, NodePathData, NodePathSerialized

SlotPairKey = tuple[str, str, str, str]
class ConnectionManager:
    _connections: dict[str, ConnectionSceneData] = {}
    _registry: TypeRegistry
    _endpoints_index: set[SlotPairKey] # TODO: pensar se a gente vai manter isso

    @property
    def conn_index(self): return self._connections

    @property
    def connections(self): return self._connections.values()

    @property
    def conn_ids(self): return self._connections.keys()

    def __init__(self, type_registry: TypeRegistry) -> None:
        self._registry = type_registry
        self._connections = {}
        self._endpoints_index = set()

    def _clear(self):
        self._connections.clear()
        self._endpoints_index.clear()

    
    def connect_slots(self, from_slot: SlotInstance, to_slot: SlotInstance, conn_uid: Optional[str] = None) -> Optional[ConnectionSceneData]:
        self.validate_connection(from_slot, to_slot)
        conn = ConnectionSceneData(
            from_slot=NodePathData(node_id=from_slot.node_id, slot_id=from_slot.slot_id),
            to_slot=NodePathData(node_id=to_slot.node_id, slot_id=to_slot.slot_id),
            uid=conn_uid or ConnectionSceneData.uid
        )

        self.add(conn)
        
        from_slot.connection_count += 1
        to_slot.connection_count += 1

        return conn

    def add(self, connection: ConnectionSceneData) -> None:
        if connection.uid in self._connections:
            raise KeyError("Another connection with the same UID already exists")

        # Assuming it already ran through validate_connection
        key = self._make_endpoint_key(connection.from_slot, connection.to_slot)
        self._connections[connection.uid] = connection
        self._endpoints_index.add(key)

    def remove(self, connection_uid: str) -> Optional[ConnectionSceneData]:
        conn = self._connections.pop(connection_uid, None)
        if conn:
            key = self._make_endpoint_key(conn.from_slot, conn.to_slot)
            self._endpoints_index.discard(key)
        
        return conn


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
        key = self._make_endpoint_key(from_slot, to_slot)
        if key in self._endpoints_index:
            raise DuplicateConnectionError(
                from_node_id=from_slot.node_id,
                from_slot_id=from_slot.slot_id,
                to_node_id=to_slot.node_id,
                to_slot_id=to_slot.slot_id,
            )
        
        if not to_slot.can_connect or not from_slot.can_connect:
            raise MaxConnectionReached(
                from_node_id=from_slot.node_id, from_slot_id=from_slot.slot_id,
                to_node_id=to_slot.node_id, to_slot_id=to_slot.slot_id
            )

        are_compatible = self._registry.are_types_compatible(
            from_slot.data_type_id, to_slot.data_type_id
        )
        if not are_compatible:
            raise IncompatibleSlotsError(
                from_node_id=from_slot.node_id, from_slot_id=from_slot.slot_id,
                to_node_id=to_slot.node_id, to_slot_id=to_slot.slot_id,
                from_datatype_id=from_slot.data_type_id, to_datatype_id=to_slot.data_type_id
            )

        existing_path = self._get_path(to_slot.node_id, from_slot.node_id)
        if existing_path:
            full_cycle_path = [from_slot.node_id] + existing_path

            raise CyclicConnectionError(
                from_node_id=from_slot.node_id,
                from_slot_id=from_slot.slot_id,
                to_node_id=to_slot.node_id,
                to_slot_id=to_slot.slot_id,
                path=full_cycle_path,
            )

    def can_connect(self, from_slot: SlotInstance, to_slot: SlotInstance) -> bool:
        try:
            self.validate_connection(from_slot, to_slot)
            return True
        except ConnectionValidationError:
            return False

    # Utils:
    def _make_endpoint_key(self, from_slot: Union[NodePathData, SlotInstance], to_slot: Union[NodePathData, SlotInstance]) -> SlotPairKey:
        return (
            from_slot.node_id,
            from_slot.slot_id,
            to_slot.node_id,
            to_slot.slot_id,
        )

    # Topology Utils

    def _get_path(self, start_node_id: str, target_node_id: str) -> list[str]:
        if start_node_id == target_node_id:
            return [start_node_id, target_node_id]

        queue: deque[tuple[str, list[str]]] = deque(
            [(start_node_id, [start_node_id])]
        )
        visited: set[str] = {start_node_id}

        while queue:
            current_id, path = queue.popleft()

            for next_node in self._get_downstream_node_ids(current_id):
                if next_node == target_node_id:
                    return path + [target_node_id]

                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [next_node]))

        return []

    def _get_downstream_node_ids(self, node_id: str) -> set[str]:
        downstream: set[str] = set()
        for conn in self._connections.values():
            if conn.from_slot.node_id == node_id:
                downstream.add(conn.to_slot.node_id)
        
        return downstream
