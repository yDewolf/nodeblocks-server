
from typing import Protocol


class NodeMirrorProtocol(Protocol):
    uid: str

class SlotMirrorProtocol(Protocol):
    parent_node: NodeMirrorProtocol
    slot_name: str
