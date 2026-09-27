from nodeserver.engine.protocols.node.logic_nodes import BaseNode, NodeInputs, NodeOutputs


class TestNodeInput(NodeInputs):
    in_0: float

class TestNodeOutputs(NodeOutputs):
    out_0: float

class TestNode(BaseNode[TestNodeInput, TestNodeOutputs]):
    InputModel = TestNodeInput
    OutputModel = TestNodeOutputs

    def forward(self, inputs: TestNodeInput) -> TestNodeOutputs:
        return TestNodeOutputs(
            out_0=inputs.in_0 + 1
        )
