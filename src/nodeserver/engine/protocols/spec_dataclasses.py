from dataclasses import dataclass

from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec
from typing import Optional, Union

# idk if it is fine to keep these two togeter but whatever
# they were 2 files with 5 lines each

@dataclass
class SlotSpecMeta:
    # Usage inside a NodeIO:
    # slot_name = Annotated[type, SlotSpecMeta(...)]
    
    datatype: Union[str, DataTypeSpec]
    max_connections: Optional[int] = None
    required: bool = False


@dataclass
class LogicNodeConfig:
    bypass_cache: bool = False
    order_independent: bool = True # TODO: implementar ordem de conexões para slots que recebem mais de uma entrada

