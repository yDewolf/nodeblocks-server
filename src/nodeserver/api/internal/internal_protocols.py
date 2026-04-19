from typing import Protocol

from nodeserver.api.instance.node_scene import NodeScene
from nodeserver.wrapper.nodes.helpers.scene_manager import MirrorSceneManager

class InstanceProtocol(Protocol):
    mirror_manager: MirrorSceneManager
    _scene: NodeScene
