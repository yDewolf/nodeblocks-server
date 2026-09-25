from tests.nodeserver.engine.conftest import MockNode

class TestNodeSpecBuilderSlots:
    def test_infer_slot_data_types_from_input_model(self, default_builder):
        slot_specs = default_builder._generate_specs_for_slots(MockNode.InputModel, is_input=True)

        assert slot_specs["text_input"].data_type_id == "core:string"
        assert slot_specs["text_input"].is_input is True

        assert slot_specs["number_list"].data_type_id == "core:int"

        assert slot_specs["optional_float"].data_type_id == "core:float"

    def test_slot_fallback_to_unknown_type(self, default_builder):
        slot_specs = default_builder._generate_specs_for_slots(MockNode.InputModel, is_input=True)

        assert slot_specs["custom_type_field"].data_type_id == "core:unknown"

    def test_slot_max_connections_defaults(self, default_builder):
        inputs = default_builder._generate_specs_for_slots(MockNode.InputModel, is_input=True)
        outputs = default_builder._generate_specs_for_slots(MockNode.OutputModel, is_input=False)

        assert inputs["text_input"].max_connections == 1
        assert inputs["number_list"].max_connections == 0
        assert outputs["result"].max_connections == 0


class TestNodeSpecBuilderParameters:
    def test_parameter_extraction(self, default_builder):
        param_specs = default_builder._generate_specs_for_parameters(MockNode.Parameters)

        assert param_specs["title"].default == "Default Title"
        assert param_specs["title"].datatype_fqn == "core:string"

        assert param_specs["factor"].default == 1.0
        assert param_specs["factor"].datatype_fqn == "core:float"

    def test_parameter_fallback_type(self, default_builder):
        param_specs = default_builder._generate_specs_for_parameters(MockNode.Parameters)
        assert param_specs["unregistered_param"].datatype_fqn == "core:unknown"


class TestNodeSpecBuilderBuildNodeSpec:
    def test_build_node_spec_from_base_node_class(self, default_builder):
        # FIXME: grab spec from registry
        node_spec = default_builder.build_node_spec("custom", "transform_node", MockNode)

        assert node_spec.namespace == "custom"
        assert node_spec.id == "transform_node"
        assert node_spec.fqn == "custom:transform_node"

        assert "text_input" in node_spec.slots
        assert "result" in node_spec.slots
        assert node_spec.slots["text_input"].is_input is True
        assert node_spec.slots["result"].is_input is False

        assert "title" in node_spec.parameters
        assert "factor" in node_spec.parameters

    def test_serialize_nodetype_spec(self, default_builder):
        node_spec = default_builder.build_node_spec("custom", "transform_node", MockNode)
        serialized = node_spec.serialize()

        assert isinstance(serialized, dict)
        assert serialized["namespace"] == "custom"
        assert serialized["id"] == "transform_node"
        assert "slots" in serialized
        assert "parameters" in serialized
