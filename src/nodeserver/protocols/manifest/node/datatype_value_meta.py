from types import NoneType
from typing import Annotated, Literal, Optional, Union

from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes
from nodeserver.protocols.manifest.base_manifest import DataModel
from pydantic import Field


ValidSerializedDataType = Union[dict, str, bool, int, float, list, tuple, NoneType]

class DataTypeValueMeta(DataModel):
    type: DefaultDataTypes

class ArrayMetadata(DataTypeValueMeta):
    type: Literal[DefaultDataTypes.ARRAY] = Field(default=DefaultDataTypes.ARRAY) # type: ignore
    shape: tuple[int, ...]

    min: Optional[float]
    max: Optional[float]


class FileMetadata(DataTypeValueMeta):
    type: Literal[DefaultDataTypes.FILE] = Field(default=DefaultDataTypes.FILE) # type: ignore
    is_artifact: bool


ValueMetadataTypes = Annotated[Union[
    ArrayMetadata, FileMetadata
], Field(discriminator="type")]

class SerializedDataTypeValue[TMetadata: ValueMetadataTypes](DataModel):
    value: ValidSerializedDataType
    metadata: Optional[TMetadata]

class NoMetaDataTypeValue(SerializedDataTypeValue):
    metadata: Optional[ValueMetadataTypes] = Field(default=None)
