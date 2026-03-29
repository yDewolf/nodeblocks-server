
from nodeserver.networking.nodes.node.base_nodes import ConnectionMirror, SlotMirror


class ConnectionManager:
    _connections: dict[str, ConnectionMirror]

    def __init__(self) -> None:
        self._connections = {}

    def clear(self):
        self._connections.clear()

    
    def get_connection(self, uid: str):
        return self._connections.get(uid)

    def remove_connection(self, uid: str) -> bool:
        conn = self.get_connection(uid)
        if not conn:
            return False
        
        self.disconnect_nodes(conn)
        return True

    def connect_nodes(self, slot_a: SlotMirror, slot_b: SlotMirror, conn_uid: str | None = None) -> bool:
        connection = ConnectionMirror(slot_a, slot_b, conn_uid)
        if not connection.is_valid():
            return False

        self._connections[connection.uid] = connection
        connection.connect()
        return True
    

    def disconnect_nodes(self, connection: ConnectionMirror):
        self._connections.pop(connection.uid)
        connection.disconnect()

    def are_connected(self, slot_a: SlotMirror, slot_b: SlotMirror) -> ConnectionMirror | None:
        return slot_a.connections.get(slot_b) 