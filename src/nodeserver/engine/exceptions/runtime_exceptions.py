from typing import Any
from pydantic import ValidationError

from nodeserver.engine.exceptions.base_exceptions import EngineDomainError


class EngineRuntimeError(EngineDomainError):
    pass

class NodeRuntimeError(EngineRuntimeError):
   node_uid: str

   def __init__(
        self, 
        node_uid: str,
        message: str,
        error_code: str = "NODE_RUNTIME_ERROR",
        extra_details: dict[str, Any] | None = None
    ) -> None:
        self.node_uid = node_uid
        super().__init__(
            error_code, 
            message,
            {"node_uid": node_uid, **(extra_details or {})}
        )


class NodeSlotRuntimeError(NodeRuntimeError):
    slot_ids: list[str]
    messages: list[str]

    def __init__(
        self, 
        node_uid: str,
        slot_ids: list[str],
        messages: list[str]
    ) -> None:
        self.slot_ids = slot_ids
        self.messages = messages
        super().__init__(
            node_uid,
            f"Error in Slots: {", ".join(slot_ids)}.",
            error_code="NODE_SLOT_ERROR",
            extra_details={"slot_ids": slot_ids, "messages": self.messages}
        )

class NodeParamRuntimeError(NodeRuntimeError):
   param_ids: list[str]
   messages: list[str]

   def __init__(
        self, 
        node_uid: str,
        param_ids: list[str],
        messages: list[str],
    ) -> None:
        self.param_ids = param_ids
        self.messages = messages
        super().__init__(
            node_uid,
            f"Error in Parameters: {", ".join(param_ids)}.",
            error_code="NODE_PARAM_ERROR",
            extra_details={"param_id": param_ids, "messages": self.messages}
        )


def extract_ids_and_messages(exception: ValidationError) -> tuple[list[str], list[str]]:
    ids: list[str] = []
    error_messages: list[str] = []
    for error in exception.errors():
        location_path = error.get("loc", [])
        error_message = error.get("msg")

        if not location_path: continue

        field_name = str(location_path[-1])
        ids.append(field_name)
        error_messages.append(error_message)
    
    return ids, error_messages
