from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict

from nodeserver.engine.protocols.spec_dataclasses import LogicNodeConfig
from nodeserver.engine.protocols.parameters.node_parameter import NodeParameters
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData

class NodeIO(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

# FIXME: arrumar typesafety dos forwards usando generics aqui
class BaseNode(ABC):
    config: LogicNodeConfig

    scene_data: NodeSceneData # Should be a reference to a NodeInstance.node_data
    class Inputs(NodeIO):
        pass

    class Outputs(NodeIO):
        pass

    InputModel: type[NodeIO] = Inputs
    OutputModel: type[NodeIO] = Outputs

    class Parameters(NodeParameters):
        pass

    params: Parameters

    def __init__(self, scene_data: NodeSceneData) -> None:
        self.scene_data = scene_data

        self.params = self.Parameters(**scene_data.data)
        self.params.bind_sync(self._on_param_changed)

    @abstractmethod
    def pre_forward(self, inputs: Inputs) -> None:
        pass

    @abstractmethod
    def forward(self, inputs: Inputs) -> Outputs:
        pass

    @abstractmethod
    def post_forward_cleanup(self):
        pass

    # TODO: reimplementar o sistema de estados
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

    def _ensure_parameters_updated(self):
        self.update_parameters(self.scene_data.data)

    # TODO: implementar os geradores de specs para datatypes, slots e parâmetros
    # para popular os registros dos plugins
