
from nodeserver.api.instance.base_nodes import AutoTypeNode, BaseNode, NodeInput, NodeOutput, NodeSlot, SlotIO
from nodeserver.wrapper.nodes.data.node_data import NodeData
from nodeserver.wrapper.nodes.data.node_data_types import INPUT_TYPE, OUTPUT_TYPE, DataTypes
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import NodeNumberParameter, NodeParameterData
from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror, SlotMirror

class NoInput(NodeInput):
    pass

class TestNode(AutoTypeNode):
    class Slots:
        in_0: NodeSlot[SlotIO[int, None]]
        out_0: NodeSlot[SlotIO[None, float]]

    def forwardV2(self, input: "TestNode.InputModel") -> "TestNode.OutputModel":
        return self.OutputModel(
            out_0=(input.in_0 + 2)
        )

class DataNodeOutput(NodeOutput):
    out_0: int

class InputDataNode(BaseNode[NoInput, DataNodeOutput]):
    class Slots:
        out_0: NodeSlot[SlotIO[None, int]]
    
    _slots: Slots

    def forwardV2(self, input: NoInput) -> DataNodeOutput:
        return DataNodeOutput(
            out_0=self._mirror.data.get_parameter_value("value", 0)
        )

mirror = NodeMirror("", NodeData({}))
# Esse INPUT_TYPE é o tipo do slot, tecnicamente, depois esse tipo seria gerado com base
# nos slots de todos os tipos de nodes e depois enviados para o client, mas atualmente a única coisa
# que influência no tipo do NodeSlot é só o nome dele, para poder relacionar com a variável no Slots
mirror.add_slot(SlotMirror(mirror, "in_0", INPUT_TYPE, None))
mirror.add_slot(SlotMirror(mirror, "out_0", OUTPUT_TYPE, None))
node = TestNode(mirror)

input_mirror = NodeMirror("", NodeData.from_model(NodeData({"value": NodeNumberParameter(type=DataTypes.INT)})))
input_mirror.data.parse_parameters({
    "value": 10
})
input_mirror.add_slot(SlotMirror(input_mirror, "out_0", OUTPUT_TYPE, None))
input_node = InputDataNode(input_mirror)

_output = input_node.forwardV2(NoInput())
_output_1 = node.forwardV2(node._parse_inputs(
    {"in_0": _output.out_0}
))

pass