
from typing import Annotated

from pydantic import BaseModel

from nodeserver.api.instance.base_nodes import NodeInput, NodeOutput, NodeSlot, SlotIO
from nodeserver.api.node.nodes import BaseNode
from nodeserver.wrapper.nodes.data.node_data import NodeData
from nodeserver.wrapper.nodes.data.node_data_types import INPUT_TYPE, OUTPUT_TYPE, DataTypes
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import NodeNumberParameter, NodeParameterData
from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror, SlotMirror

class NoInput(NodeInput):
    pass

class MyCustomInputs(BaseModel):
    in_0: float
    # value_b: Annotated[int, Input(min_val=0)]

class MyCustomOutputs(NodeOutput):
    result: float

class MyMathNode(BaseNode[MyCustomInputs, MyCustomOutputs]):
    InputModel = MyCustomInputs
    OutputModel = MyCustomOutputs 

    def forward(self, input_data: MyCustomInputs) -> MyCustomOutputs:
        return MyCustomOutputs(
            result=input_data.in_0 + 2.0
        )

class DataNodeOutput(NodeOutput):
    out_0: int

class InputDataNode(BaseNode[NoInput, DataNodeOutput]):
    InputModel = NoInput
    OutputModel = DataNodeOutput
    
    def forward(self, input: NoInput) -> DataNodeOutput:
        return DataNodeOutput(
            out_0=self._mirror.data.get_parameter_value("value", 0)
        )

mirror = NodeMirror("", NodeData({}))
# Esse INPUT_TYPE é o tipo do slot, tecnicamente, depois esse tipo seria gerado com base
# nos slots de todos os tipos de nodes e depois enviados para o client, mas atualmente a única coisa
# que influência no tipo do NodeSlot é só o nome dele, para poder relacionar com a variável no Slots
mirror.add_slot(SlotMirror(mirror, "in_0", INPUT_TYPE, None))
mirror.add_slot(SlotMirror(mirror, "out_0", OUTPUT_TYPE, None))
node = MyMathNode(mirror)

input_mirror = NodeMirror("", NodeData.from_model(NodeData({"value": NodeNumberParameter(type=DataTypes.INT)})))
input_mirror.data.parse_parameters({
    "value": 10
})
input_mirror.add_slot(SlotMirror(input_mirror, "out_0", OUTPUT_TYPE, None))
input_node = InputDataNode(input_mirror)

_output = input_node.forward(NoInput())
_output_1 = node.forward(node._parse_inputs(
    {"in_0": _output.out_0}
)) # type: ignore

pass