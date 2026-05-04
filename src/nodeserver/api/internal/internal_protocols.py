from typing import Protocol

from nodeserver.api.instance.node_scene import NodeScene
from nodeserver.api.web.requests.request_unions import AnyServerMessage
from nodeserver.wrapper.nodes.helpers.scene_manager import MirrorSceneManager

class InstanceProtocol(Protocol):
    mirror_manager: MirrorSceneManager
    _scene: NodeScene
    
    _attributed_id: str

    def send_to_client(self, message: AnyServerMessage) -> None:
        pass


class WorkspaceProtocol(Protocol):
    user_id: str
    workspace_path: str
