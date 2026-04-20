import uuid

class IDGenerator:
    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def generate_node_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def generate_conn_id() -> str:
        return f"{uuid.uuid4().hex[:8]}"
    
    @staticmethod
    def generate_session_id() -> str:
        return f"sess_{uuid.uuid4().hex[:8]}"