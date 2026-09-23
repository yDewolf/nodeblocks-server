from abc import ABC, abstractmethod
from typing import Any

from nodeserver.engine.protocols.node_instance import NodeInstance


class BaseNode(ABC):
    instance: NodeInstance

    def __init__(self, instance: NodeInstance) -> None:
        self.instance = instance

    # TODO: implementar typesafety nos inputs e outpus de novo
    @abstractmethod
    def forward(self, inputs: dict[str, Any]) -> dict[str, Any]:
        pass

    def load_state(self, state: dict[str, Any]) -> None:
        pass

    def save_state(self) -> dict[str, Any]:
        return {}
