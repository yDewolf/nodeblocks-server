import pytest
from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers
from nodeserver.protocols.helpers.datatype_helper import DatatypeHelper
from tests.nodeserver.engine.conftest import CustomType
from tests.nodeserver.engine.node_spec_builder_test import MockNode


class TestNodeSpecBuilderCustomTypeRegistration:
    def test_custom_type_resolves_correctly_when_registered(self, default_registry, default_builder):
        custom_spec = DatatypeHelper.create_spec(
            namespace="custom",
            id="custom_type",
            base_id=DefaultDataTypes.UNKNOWN,
            renderer=DefaultRenderers.NOT_IMPLEMENTED,
        )
        default_registry.register_data_type(custom_spec, python_type=CustomType)

        assert default_registry.get_datatype_by_annotation(CustomType) == custom_spec

        slot_specs = default_builder._generate_specs_for_slots(MockNode.InputModel, is_input=True)
        assert slot_specs["custom_type_field"].data_type_id == "custom:custom_type"

        param_specs = default_builder._generate_specs_for_parameters(MockNode.Parameters)
        assert param_specs["unregistered_param"].datatype_fqn == "custom:custom_type"


class TestTypeRegistryCustomNodeRegistration:
    def test_register_custom_node_type_success(self, default_registry, default_builder):
        namespace = "custom"
        node_id = "transform_node"
        fqn = f"{namespace}:{node_id}"

        node_spec = default_builder.build_node_spec(namespace, node_id, MockNode)
        default_registry.register_node_type(node_spec, logic_class=MockNode)

        retrieved_spec = default_registry.get_node_type_spec(fqn)
        assert retrieved_spec == node_spec
        assert retrieved_spec.namespace == namespace
        assert retrieved_spec.id == node_id
        assert retrieved_spec.fqn == fqn

        retrieved_logic_class = default_registry.get_logic_class(fqn)
        assert retrieved_logic_class == MockNode

    def test_register_duplicate_node_type_raises_value_error(self, default_registry, default_builder):
        node_spec = default_builder.build_node_spec("custom", "transform_node", MockNode)
        default_registry.register_node_type(node_spec, logic_class=MockNode)

        with pytest.raises(ValueError):
            default_registry.register_node_type(node_spec, logic_class=MockNode)

    def test_get_unregistered_node_spec_raises_key_error(self, default_registry):
        with pytest.raises(KeyError):
            default_registry.get_node_type_spec("non_existent:node")

    def test_get_unregistered_logic_class_raises_key_error(self, default_registry):
        with pytest.raises(KeyError):
            default_registry.get_logic_class("non_existent:node")
