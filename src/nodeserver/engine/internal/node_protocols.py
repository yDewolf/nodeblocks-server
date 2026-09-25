
from typing import Optional, Protocol

from nodeserver.protocols.manifest.node.datatypes import ParameterSpec


class NodeMirrorProtocol(Protocol):
    uid: str

class NodeParameterProtocol(Protocol):
    _data_model: ParameterSpec
    _field_id: str

class SlotMirrorProtocol(Protocol):
    parent_node: NodeMirrorProtocol
    slot_id: str
