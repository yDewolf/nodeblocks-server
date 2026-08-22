
from typing import Optional, Protocol

from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import NodeParameterData


class NodeMirrorProtocol(Protocol):
    uid: str

class NodeParameterProtocol(Protocol):
    _data_model: NodeParameterData
    _field_id: str

class SlotMirrorProtocol(Protocol):
    parent_node: NodeMirrorProtocol
    slot_id: str
