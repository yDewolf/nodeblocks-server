from dataclasses import dataclass
from typing import Optional, Union

from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec

@dataclass
class SlotSpecMeta:
    datatype: Union[str, DataTypeSpec]
    max_connections: Optional[int] = None

# Usage:
# Annotated[type, SlotSpecMeta(...)]
