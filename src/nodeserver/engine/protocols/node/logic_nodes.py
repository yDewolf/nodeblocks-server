from abc import ABC, abstractmethod
from typing import ClassVar, Any, Optional

from pydantic import BaseModel, ConfigDict

from nodeserver.engine.protocols.node.scene_states import LogicNodeState
from nodeserver.engine.protocols.scene_state_provider import ISceneStateProvider
from nodeserver.engine.protocols.spec_dataclasses import LogicNodeConfig
from nodeserver.engine.protocols.parameters.node_parameter import NodeParameters
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData

class NodeIO(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

class NodeInputs(NodeIO): pass
class NodeOutputs(NodeIO): pass


class BaseNode[inputModel: NodeInputs, outputModel: NodeOutputs](ABC):
    config: LogicNodeConfig = LogicNodeConfig()

    scene_data: NodeSceneData # Should be a reference to a NodeInstance.node_data
    InputModel: ClassVar[type[NodeInputs]] = NodeInputs
    OutputModel: ClassVar[type[NodeOutputs]] = NodeOutputs
    
    class Parameters(NodeParameters):
        pass
    
    params: Parameters

    def __init__(self, scene_data: NodeSceneData) -> None:
        self.scene_data = scene_data

        self.params = self.Parameters(**scene_data.data)
        self.params.bind_sync(self._on_param_changed)

    def pre_forward(self, inputs: inputModel) -> None:
        pass

    @abstractmethod
    def forward(self, inputs: inputModel) -> outputModel:
        pass

    def post_forward_cleanup(self):
        pass

    def load_state(self, state: LogicNodeState) -> None:
        """
        Load your custom files or your state data
        """
        pass
    
    def save_state(self, state_provider: ISceneStateProvider) -> Optional[LogicNodeState]:
        """
        Use state_provider to get a path where you can save your node state if you need it

        Example Usage:
        ```
        states_folder = state_provider.get_node_state_folder(self.scene_data.uid)
        with open(states_folder / "my_save.md", "w") as file:
            file.write("Some data you can't save in a .json file")

        return LogicNodeState(
            extra_files={"my_file": states_folder / "my_save.md"},
            state_data={"some_state": 900, "another": "state"}
        )
        ```
        """
        pass


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
