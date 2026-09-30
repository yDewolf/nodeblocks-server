import pytest


from nodeserver.engine.helpers.node_instance_factory import NodeInstanceFactory
from nodeserver.engine import BaseNode
from nodeserver.engine.protocols.node.node_instance import NodeInstance, SlotInstance
from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers
from nodeserver.protocols.helpers.datatype_helper import DatatypeHelper
from nodeserver.protocols.manifest.node.node_graph import NodeSceneData
from tests.nodeserver.engine.conftest import CustomType, MockNode


@pytest.fixture
def factory_with_registered_node(default_registry, default_builder):
    namespace = "custom"
    node_id = "transform_node"

    default_registry.register_data_type(
        DatatypeHelper.create_spec("custom", "custom_type", DefaultDataTypes.CUSTOM, DefaultRenderers.NOT_IMPLEMENTED),
        python_type=CustomType
    )

    spec = default_builder.build_node_spec(namespace, node_id, MockNode)
    default_registry.register_node_type(spec, logic_class=MockNode)

    return NodeInstanceFactory(default_registry), spec


class TestNodeInstanceFactory:
    def test_create_node_instance_with_default_data(self, factory_with_registered_node):
        factory, spec = factory_with_registered_node
        fqn = spec.fqn

        node_instance, logic_instance = factory.create(fqn)

        assert isinstance(node_instance, NodeInstance)
        assert isinstance(logic_instance, BaseNode)
        assert isinstance(logic_instance, MockNode)

        assert node_instance.node_data.type_id == fqn
        assert node_instance.node_data.uid is not None
        assert node_instance.node_data.data["title"] == "Default Title"
        assert node_instance.node_data.data["factor"] == 1.0

        assert logic_instance.scene_data is node_instance.node_data
        assert logic_instance.params.title == "Default Title"
        assert logic_instance.params.factor == 1.0

        assert set(node_instance.slots.keys()) == set(spec.slots.keys())
        for slot_id, slot_instance in node_instance.slots.items():
            assert isinstance(slot_instance, SlotInstance)
            assert slot_instance.node_id == node_instance.uid
            assert slot_instance.slot_id == slot_id
            assert slot_instance.spec == spec.slots[slot_id]

    def test_create_node_instance_with_custom_scene_data(self, factory_with_registered_node):
        factory, spec = factory_with_registered_node
        fqn = spec.fqn

        custom_scene_data = NodeSceneData(
            uid="node_custom_123",
            type_id=fqn,
            data={"title": "Custom Title", "factor": 5.5, "unregistered_param": None},
        )

        node_instance, logic_instance = factory.create(fqn, node_scene_data=custom_scene_data)

        assert node_instance.uid == "node_custom_123"
        assert node_instance.node_data.data["title"] == "Custom Title"
        assert node_instance.node_data.data["factor"] == 5.5

        assert logic_instance.params.title == "Custom Title"
        assert logic_instance.params.factor == 5.5

    def test_create_unregistered_node_type_raises_value_error(self, default_registry):
        factory = NodeInstanceFactory(default_registry)

        with pytest.raises((ValueError, KeyError)):
            factory.create("unregistered:node_type")