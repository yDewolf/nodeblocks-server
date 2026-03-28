
from nodeserver.networking.nodes.node.base_nodes import ConnectionMirror, SlotMirror


class ConnectionManager:
    _connections: list[ConnectionMirror]

    def __init__(self) -> None:
        self._connections = []

    def clear(self):
        self._connections.clear()

    
    def connect_nodes(self, slot_a: SlotMirror, slot_b: SlotMirror) -> bool:
        connection = ConnectionMirror(slot_a, slot_b)
        if not connection.is_valid():
            return False

        self._connections.append(connection)
        connection.connect()
        return True
    

    def disconnect_nodes(self, connection: ConnectionMirror):
        self._connections.remove(connection)
        connection.disconnect()

    def are_connected(self, slot_a: SlotMirror, slot_b: SlotMirror) -> ConnectionMirror | None:
        return slot_a.connections.get(slot_b) 