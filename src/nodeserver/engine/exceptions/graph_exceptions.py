from typing import Any, Optional

from nodeserver.engine.exceptions.base_exceptions import EngineDomainError

class GraphDomainError(EngineDomainError):
    pass

# Node manager

class DuplicateNodeUIDError(EngineDomainError):
    def __init__(
        self,
        node_uid: str,
    ) -> None:
        super().__init__(
            error_code="DUPLICATE_NODE", 
            message="Another node is registered with the same UID", 
            details={"node_uid": node_uid}
        )


# ConnectionManager

class ConnectionValidationError(GraphDomainError):
    def __init__(
        self,
        error_code: str,
        message: str,
        from_node_id: str,
        from_slot_id: str,
        to_node_id: str,
        to_slot_id: str,
        **extra_details: Any,
    ) -> None:
        details = {
            "from_node_id": from_node_id,
            "from_slot_id": from_slot_id,
            "to_node_id": to_node_id,
            "to_slot_id": to_slot_id,
            **extra_details,
        }
        super().__init__(error_code=error_code, message=message, details=details)

class IncompatibleSlotsError(ConnectionValidationError):
    def __init__(
        self,
        from_node_id: str,
        from_slot_id: str,
        to_node_id: str,
        to_slot_id: str,
        from_datatype_id: str,
        to_datatype_id: str
    ) -> None:
        super().__init__(
            error_code="INCOMPATIBLE_DATATYPE",
            message=f"Incompatible types: {from_datatype_id} -> {to_datatype_id}",
            from_node_id=from_node_id,
            from_slot_id=from_slot_id,
            to_node_id=to_node_id,
            to_slot_id=to_slot_id,
            extra_details={"from_datatype": from_datatype_id, "to_datatype": to_datatype_id}
        )

class MaxConnectionReached(ConnectionValidationError):
    def __init__(
        self,
        from_node_id: str,
        from_slot_id: str,
        to_node_id: str,
        to_slot_id: str,
    ) -> None:
        super().__init__(
            error_code="MAX_CONNECTIONS_REACHED",
            message=f"One of the slots already reached its max connections",
            from_node_id=from_node_id,
            from_slot_id=from_slot_id,
            to_node_id=to_node_id,
            to_slot_id=to_slot_id,
        )

class CyclicConnectionError(ConnectionValidationError):
    def __init__(
        self,
        from_node_id: str,
        from_slot_id: str,
        to_node_id: str,
        to_slot_id: str,
        path: list[str]
    ) -> None:
        super().__init__(
            error_code="CYCLIC_CONNECTION",
            message=f"Cyclic path found between {from_node_id}:{from_slot_id} and {to_node_id}:{to_slot_id}: {"->".join([uid[-4:] for uid in path])}",
            from_node_id=from_node_id,
            from_slot_id=from_slot_id,
            to_node_id=to_node_id,
            to_slot_id=to_slot_id,
            extra_details={"conn_path": path}
        )

class DuplicateConnectionError(ConnectionValidationError):
  def __init__(
      self,
      from_node_id: str,
      from_slot_id: str,
      to_node_id: str,
      to_slot_id: str,
  ):
    super().__init__(
        error_code="DUPLICATE_CONNECTION",
        message="Another identical connection already exists",
        from_node_id=from_node_id,
        from_slot_id=from_slot_id,
        to_node_id=to_node_id,
        to_slot_id=to_slot_id,
    )


# SceneGraph

class CyclicGraphError(GraphDomainError):
    def __init__(
        self,
        unprocessed_nodes: list[str] | None = None,
    ) -> None:
        self.unprocessed_nodes = unprocessed_nodes or []
        super().__init__(
            error_code="CYCLIC_GRAPH",
            message=f"Circular dependency detected involving nodes: {unprocessed_nodes}",
            details={"unprocessed_nodes": self.unprocessed_nodes}
        )

