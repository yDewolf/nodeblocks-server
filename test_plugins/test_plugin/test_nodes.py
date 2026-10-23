from typing import Annotated

from nodeserver.engine.plugins.api.decorators.plugin_decorators import plugin_node
from nodeserver.engine.protocols.node.logic_nodes import BaseNode, NodeInputs, NodeOutputs
from nodeserver.engine.protocols.parameters.node_parameter import NodeParameters
from nodeserver.engine.protocols.parameters.param_wrappers import Param
from test_plugin.test_datatypes import TestDatatype


class TestNodeInput(NodeInputs):
    in_0: float = 0.0

class TestNodeOutputs(NodeOutputs):
    out_0: float
    test_out: TestDatatype

@plugin_node()
class TestNode(BaseNode[TestNodeInput, TestNodeOutputs]):
    InputModel = TestNodeInput
    OutputModel = TestNodeOutputs

    def forward(self, inputs: TestNodeInput) -> TestNodeOutputs:
        return TestNodeOutputs(
            out_0=inputs.in_0 + 1,
            test_out=TestDatatype(value=10)
        )

class TestNodeParamOut(NodeOutputs):
    out_0: int

@plugin_node()
class TestNodeParameter(BaseNode[NodeInputs, TestNodeParamOut]):
    InputModel = NodeInputs
    OutputModel = TestNodeParamOut

    class Parameters(NodeParameters):
        value: Annotated[int, Param()] = 10

    params: Parameters

    def forward(self, inputs: NodeInputs) -> TestNodeParamOut:
        return TestNodeParamOut(
            out_0=self.params.value
        )
