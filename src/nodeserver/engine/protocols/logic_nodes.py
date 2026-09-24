from abc import ABC, abstractmethod
from typing import Any

from nodeserver.engine.protocols.parameters.node_parameter import NodeParameters
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData


class BaseNode(ABC):
    scene_data: NodeSceneData # Should be a reference to a NodeInstance.node_data
    class Parameters(NodeParameters):
        pass

    params: Parameters

    def __init__(self, scene_data: NodeSceneData) -> None:
        self.scene_data = scene_data

        self.params = self.Parameters(**scene_data.data)
        self.params.bind_sync(self._on_param_changed)

    # TODO: implementar typesafety nos inputs e outpus de novo
    @abstractmethod
    def forward(self, inputs: dict[str, Any]) -> dict[str, Any]:
        pass

    def load_state(self, state: dict[str, Any]) -> None:
        pass

    def save_state(self):
        return


    def update_parameters(self, new_params: dict[str, Any]) -> dict[str, Any]:
        current_data = self.params.model_dump()
        merged_data = {**current_data, **new_params}

        validated_params = self.params.__class__(**merged_data) # TODO: talvez pensar em um jeito de não recriar o objeto

        self.params = validated_params 
        self.params.bind_sync(self._on_param_changed)

        self.scene_data.data = validated_params.model_dump()
        return self.scene_data.data

    def _on_param_changed(self, param_name: str, new_value: Any) -> None:
        self.scene_data.data[param_name] = new_value
