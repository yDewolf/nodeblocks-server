from abc import ABC
from types import NoneType
from typing import Optional, TypedDict, Union

from pydantic import Field
from pydantic.dataclasses import dataclass


ValidSerializedDataType = Union[dict, str, bool, int, float, list, tuple, NoneType]

@dataclass
class ArrayMetadata:
    shape: tuple[int, ...]

    min: Optional[float]
    max: Optional[float]


ValueMetadataTypes = Union[
    ArrayMetadata, NoneType
]

@dataclass
class SerializedDataTypeValue[TMetadata: ValueMetadataTypes](ABC):
    value: ValidSerializedDataType
    metadata: TMetadata

@dataclass
class NoMetaDataTypeValue(SerializedDataTypeValue[NoneType]):
    metadata: NoneType = Field(default=None)
