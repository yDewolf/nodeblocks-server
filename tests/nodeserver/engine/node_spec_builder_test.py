from typing import Optional
import pytest
from pydantic import BaseModel, Field

from nodeserver.engine import NodeInputs, NodeOutputs, BaseNode
from nodeserver.engine import NodeParameters
from nodeserver.engine import TypeRegistry
from nodeserver.engine import NodeSpecBuilder
from nodeserver.protocols import DataTypeSpec
from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers
from nodeserver.protocols.helpers.datatype_helper import DatatypeHelper

class CustomType:
    """Tipo Python não registrado no TypeRegistry."""
    pass


# --- Modelos de Entrada, Saída e Parâmetros do Nó ---

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
def registry():
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
def builder(registry):
    return NodeSpecBuilder(registry)


class TestNodeSpecBuilderSlots:
    def test_infer_slot_data_types_from_input_model(self, builder):
        slot_specs = builder._generate_specs_for_slots(MockNode.InputModel, is_input=True)

        assert slot_specs["text_input"].data_type_id == "core:string"
        assert slot_specs["text_input"].is_input is True

        assert slot_specs["number_list"].data_type_id == "core:int"

        assert slot_specs["optional_float"].data_type_id == "core:float"

    def test_slot_fallback_to_unknown_type(self, builder):
        slot_specs = builder._generate_specs_for_slots(MockNode.InputModel, is_input=True)

        assert slot_specs["custom_type_field"].data_type_id == "core:unknown"

    def test_slot_max_connections_defaults(self, builder):
        inputs = builder._generate_specs_for_slots(MockNode.InputModel, is_input=True)
        outputs = builder._generate_specs_for_slots(MockNode.OutputModel, is_input=False)

        assert inputs["text_input"].max_connections == 1
        assert inputs["number_list"].max_connections == 0
        assert outputs["result"].max_connections == 0


class TestNodeSpecBuilderParameters:
    def test_parameter_extraction(self, builder):
        param_specs = builder._generate_specs_for_parameters(MockNode.Parameters)

        assert param_specs["title"].default == "Default Title"
        assert param_specs["title"].datatype_fqn == "core:string"

        assert param_specs["factor"].default == 1.0
        assert param_specs["factor"].datatype_fqn == "core:float"

    def test_parameter_fallback_type(self, builder):
        param_specs = builder._generate_specs_for_parameters(MockNode.Parameters)
        assert param_specs["unregistered_param"].datatype_fqn == "core:unknown"


class TestNodeSpecBuilderBuildNodeSpec:
    def test_build_node_spec_from_base_node_class(self, builder):
        # FIXME: grab spec from registry
        node_spec = builder.build_node_spec("custom", "transform_node", MockNode)

        assert node_spec.namespace == "custom"
        assert node_spec.id == "transform_node"
        assert node_spec.fqn == "custom:transform_node"

        assert "text_input" in node_spec.slots
        assert "result" in node_spec.slots
        assert node_spec.slots["text_input"].is_input is True
        assert node_spec.slots["result"].is_input is False

        assert "title" in node_spec.parameters
        assert "factor" in node_spec.parameters

    def test_serialize_nodetype_spec(self, builder):
        node_spec = builder.build_node_spec("custom", "transform_node", MockNode)
        serialized = node_spec.serialize()

        assert isinstance(serialized, dict)
        assert serialized["namespace"] == "custom"
        assert serialized["id"] == "transform_node"
        assert "slots" in serialized
        assert "parameters" in serialized