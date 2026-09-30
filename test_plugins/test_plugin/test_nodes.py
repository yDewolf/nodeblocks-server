from nodeserver.engine.plugins.api.decorators.plugin_decorators import plugin_node
from nodeserver.engine.protocols.node.logic_nodes import BaseNode, NodeInputs, NodeOutputs
from test_plugins.test_plugin.test_datatypes import TestDatatype


class TestNodeInput(NodeInputs):
    in_0: float

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
            test_out=TestDatatype()
        )
