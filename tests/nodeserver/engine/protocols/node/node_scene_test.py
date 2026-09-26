import pytest

from nodeserver.engine.exceptions.graph_exceptions import CyclicConnectionError, CyclicGraphError, MaxConnectionReached
from nodeserver.engine.helpers.node_instance_factory import NodeInstanceFactory
from nodeserver.engine.protocols.node.node_scene import NodeScene
from tests.nodeserver.engine.conftest import MockNode

@pytest.fixture
def scene_setup(default_registry, default_builder) -> tuple[NodeScene, NodeInstanceFactory, str]:
    spec = default_builder.build_node_spec("custom", "transform_node", MockNode)
    default_registry.register_node_type(spec, logic_class=MockNode)

    factory = NodeInstanceFactory(default_registry)
    scene = NodeScene(registry=default_registry, factory=factory)

    return scene, factory, spec.fqn


class TestNodeSceneManagement:
    def test_remove_node_cleans_up_connections(self, scene_setup):
        scene, factory, node_fqn = scene_setup

        node1 = scene.create_node(node_fqn)
        node2 = scene.create_node(node_fqn)

        scene.graph.connect(
            from_node_id=node1.uid,
            from_slot_id="result",
            to_node_id=node2.uid,
            to_slot_id="text_input"
        )

        assert len(scene.graph.all_connections) == 1

        scene.delete_node(node1.uid)

        assert node1.uid not in scene.graph.all_nodes
        assert len(scene.graph.all_connections) == 0


class TestSceneGraphConnections:
    def test_add_and_remove_valid_connection(self, scene_setup):
        scene, factory, node_fqn = scene_setup

        node1 = scene.create_node(node_fqn)
        node2 = scene.create_node(node_fqn)

        conn = scene.graph.connect(
            from_node_id=node1.uid,
            from_slot_id="result",
            to_node_id=node2.uid,
            to_slot_id="text_input"
        )
        assert conn.uid in scene.graph._connections.conn_ids

        scene.graph.disconnect(conn.uid)
        assert conn.uid not in scene.graph._connections.connections

    def test_prevent_duplicate_connection(self, scene_setup):
        scene, factory, node_fqn = scene_setup

        node_a = scene.create_node(node_fqn)
        node_b = scene.create_node(node_fqn)
        scene.graph.connect(
            from_node_id=node_a.uid,
            from_slot_id="result",
            to_node_id=node_b.uid,
            to_slot_id="text_input",
        )

        with pytest.raises((ValueError, KeyError)):
            scene.graph.connect(
                from_node_id=node_a.uid,
                from_slot_id="result",
                to_node_id=node_b.uid,
                to_slot_id="text_input",
            )

    def test_max_connections_limit_validation(self, scene_setup):
        scene, factory, node_fqn = scene_setup

        node_src1 = scene.create_node(node_fqn)
        node_src2 = scene.create_node(node_fqn)
        node_dst = scene.create_node(node_fqn)

        scene.graph.connect(
            from_node_id=node_src1.uid,
            from_slot_id="result",
            to_node_id=node_dst.uid,
            to_slot_id="text_input"
        )

        with pytest.raises(MaxConnectionReached):
            scene.graph.connect(
                from_node_id=node_src2.uid,
                from_slot_id="result",
                to_node_id=node_dst.uid,
                to_slot_id="text_input",
            )


class TestSceneGraphTopology:
    def test_topological_sort_linear_pipeline(self, scene_setup):
        scene, factory, node_fqn = scene_setup

        node_a = scene.create_node(node_fqn)
        node_b = scene.create_node(node_fqn)
        node_c = scene.create_node(node_fqn)

        scene.graph.connect(
            from_node_id=node_a.uid, from_slot_id="result",
            to_node_id=node_b.uid, to_slot_id="text_input"
        )
        scene.graph.connect(
            from_node_id=node_b.uid, from_slot_id="result",
            to_node_id=node_c.uid, to_slot_id="text_input"
        )

        execution_order = scene.graph.get_execution_order()

        node_uids = [node.uid for node in execution_order]
        assert node_uids.index(node_a.uid) < node_uids.index(node_b.uid)
        assert node_uids.index(node_b.uid) < node_uids.index(node_c.uid)

    def test_detect_cycle_in_graph(self, scene_setup):
        scene, factory, node_fqn = scene_setup

        node_a = scene.create_node(node_fqn)
        node_b = scene.create_node(node_fqn)

        scene.graph.connect(
            from_node_id=node_a.uid, from_slot_id="result",
            to_node_id=node_b.uid, to_slot_id="text_input"
        )

        with pytest.raises(CyclicConnectionError):
            scene.graph.connect(
                from_node_id=node_b.uid, from_slot_id="result",
                to_node_id=node_a.uid, to_slot_id="text_input"
            )
