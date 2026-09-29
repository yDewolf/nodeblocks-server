from abc import ABC, abstractmethod
from types import NoneType
from typing import Union

# Abstract classes

ValidSerializedDataType = Union[dict, str, bool, int, float, list, tuple, NoneType]

class PluginDatatype(ABC):
    # TODO: pensar certinho em como vamos fazer essa serialização
    @abstractmethod
    def serialize(self) -> ValidSerializedDataType:
        """
        Method used by the server to serialize custom plugin DataTypes.
        This method must return a value that can be stored in a json string.

        Returns:
            ValidSerializedDataType: value that would be sent to the client
        """
        raise NotImplementedError(
            f"Plugin DataType ({self.__class__.__name__}) must implement serialize method."
        )

