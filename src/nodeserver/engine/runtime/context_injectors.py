from typing import Any, Optional

from nodeserver.engine.protocols.node.logic_nodes import NodeInputs
from nodeserver.engine.protocols.node.node_scene import NodeScene
from nodeserver.engine.protocols.providers.scene_artifact_provider import ISceneArtifactProvider
from nodeserver.engine.runtime.extra_node_io import HashAwareInput
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


# -- Workspace Injector

class ArtifactAwareInput(HashAwareInput):
    scene_artifacts: ISceneArtifactProvider

class SceneArtifactInjector(ContextInjector):
    artifact_provider: Optional[ISceneArtifactProvider] = None
    def __init__(self, artifact_provider: ISceneArtifactProvider) -> None:
        super().__init__()
        self.artifact_provider = artifact_provider

    def inject_context(self, raw_inputs: dict[str, Any], InputModel: type[NodeInputs]):
        if not self.artifact_provider:
            return
        
        if issubclass(InputModel, ArtifactAwareInput):
            raw_inputs["scene_artifacts"] = self.artifact_provider

