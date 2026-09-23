
from typing import Optional, Protocol

from nodeserver.protocols.manifest.node.type_data import NodeParameterData


class NodeMirrorProtocol(Protocol):
    uid: str

class NodeParameterProtocol(Protocol):
    _data_model: NodeParameterData
    _field_id: str

class SlotMirrorProtocol(Protocol):
    parent_node: NodeMirrorProtocol
    slot_id: str
