from typing import Any, Optional

from nodeserver.engine.protocols.node.logic_nodes import NodeInputs
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.runtime.protocols.engine_context import ContextInjector
from pydantic import Field


# FIXME: isolar o contexto ao invés de passar a cena inteira lol
class SceneAwareInput(NodeInputs):
    scene_context: NodeScene = Field(exclude=True)


class SceneContextInjector(ContextInjector):
    def __init__(self, scene: Optional[NodeScene]) -> None:
        super().__init__()
        self.scene = scene

    def inject_context(self, raw_inputs: dict[str, Any], InputModel: type[NodeInputs]):
        if not self.scene:
            return
        
        if issubclass(InputModel, SceneAwareInput):
            raw_inputs["scene_context"] = self.scene
