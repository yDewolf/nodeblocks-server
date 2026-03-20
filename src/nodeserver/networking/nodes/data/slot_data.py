
from dataclasses import dataclass


@dataclass
class SlotData:
    type: str
    data_type: str | None