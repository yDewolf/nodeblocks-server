from typing import Optional

from pydantic import Field
import pytest

from nodeserver.engine import NodeInputs, NodeOutputs, BaseNode
from nodeserver.engine import NodeParameters
from nodeserver.engine import TypeRegistry
from nodeserver.engine import NodeSpecBuilder
from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers
from nodeserver.protocols.helpers.datatype_helper import DatatypeHelper

class CustomType:
    pass


class MockInputModel(NodeInputs):
    text_input: str
    number_list: list[int]
    optional_float: Optional[float] = None
    custom_type_field: CustomType


class MockOutputModel(NodeOutputs):
    result: str


class MockParametersModel(NodeParameters):
    title: str = Field(default="Default Title", title="Node Title")
    factor: float = Field(default=1.0)
    unregistered_param: Optional[CustomType] = None


class MockNode(BaseNode):
    InputModel = MockInputModel
    OutputModel = MockOutputModel
    Parameters = MockParametersModel

    def pre_forward(self, inputs: NodeInputs) -> None:
        pass

    def forward(self, inputs: NodeInputs) -> NodeOutputs:
        return MockOutputModel(result="ok")

    def post_forward_cleanup(self):
        pass


@pytest.fixture
def default_registry():
    reg = TypeRegistry()
    namespace = "core"

    reg.register_data_type(
        DatatypeHelper.create_spec(namespace, "string", base_id=DefaultDataTypes.TEXT, renderer=DefaultRenderers.TEXT),
        python_type=str
    )
    reg.register_data_type(
        DatatypeHelper.create_spec(namespace, "int", base_id=DefaultDataTypes.INT, renderer=DefaultRenderers.SCALAR),
        python_type=int
    )
    reg.register_data_type(
        DatatypeHelper.create_spec(namespace, "float", base_id=DefaultDataTypes.FLOAT, renderer=DefaultRenderers.SCALAR),
        python_type=float
    )
    reg.register_data_type(
        DatatypeHelper.create_spec(namespace, "unknown", base_id=DefaultDataTypes.UNKNOWN, renderer=DefaultRenderers.NOT_IMPLEMENTED)
    )

    return reg


@pytest.fixture
def default_builder(default_registry):
    return NodeSpecBuilder(default_registry)
