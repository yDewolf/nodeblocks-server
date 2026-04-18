from typing import Protocol

from nodeserver.api.node_scene import NodeScene
from nodeserver.networking.nodes.helpers.scene_manager import MirrorSceneManager

class InstanceProtocol(Protocol):
    mirror_manager: MirrorSceneManager
    _scene: NodeScene
