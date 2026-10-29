from abc import ABC, abstractmethod
from typing import Any

from nodeserver.protocols.manifest.node.datatype_value_meta import SerializedDataTypeValue, ValueMetadataTypes

# Abstract classes

class PluginDatatype[MetadataType: ValueMetadataTypes](ABC):
    @abstractmethod
    def serialize(self) -> SerializedDataTypeValue[MetadataType]:
        """
        Method used by the server to serialize custom plugin DataTypes.
        This method must return a value that can be stored in a json string.

        Returns:
            SerializeDataTypeValue: value that would be sent to the client
        """
        raise NotImplementedError(
            f"Plugin DataType ({self.__class__.__name__}) must implement serialize method."
        )

    @classmethod
    @abstractmethod
    def serialize_value(cls, value: Any) -> SerializedDataTypeValue[MetadataType]:
        """
        Method used by the server to serialize a slot output value
        This method must return a value that can be stored in a json string.

        Returns:
            SerializeDataTypeValue: value that would be sent to the client
        """
        raise NotImplementedError(
            f"Plugin DataType ({cls.__name__}) must implement serialize method."
        )
