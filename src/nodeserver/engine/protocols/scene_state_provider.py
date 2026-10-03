from abc import abstractmethod
from pathlib import Path
from typing import Optional, Protocol

from nodeserver.engine.protocols.node.scene_states import LogicNodeState

class ISceneStateProvider(Protocol):
    _scene_uid: str
    @property
    def scene_uid(self): return self._scene_uid
    
    def __init__(self, scene_uid: str) -> None:
        self._scene_uid = scene_uid

    @abstractmethod
    def _setup_folder(self): pass

    @abstractmethod
    def _save_node_state(self, node_uid: str, node_state: LogicNodeState): pass

    @abstractmethod
    def _load_node_state(self, node_uid: str) -> Optional[LogicNodeState]: pass

    @abstractmethod
    def get_node_state_folder(self, node_uid: str) -> Path:
        """Returns a folder path that a node might use to save its data in"""
        pass


class NoSceneStateProvider(ISceneStateProvider):
    def _setup_folder(self):
        raise NotImplementedError()

    def _save_node_state(self, node_uid: str, node_state: LogicNodeState):
        raise NotImplementedError()

    def _load_node_state(self, node_uid: str) -> LogicNodeState | None:
        raise NotImplementedError()

    def get_node_state_folder(self, node_uid: str) -> Path:
        raise NotImplementedError()
