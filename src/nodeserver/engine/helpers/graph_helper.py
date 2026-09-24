from collections import deque

from nodeserver.engine.protocols.node_instance import NodeInstance
from nodeserver.engine.protocols.node_scene import NodeScene


class NodeGraphHelper:
    @staticmethod
    def _get_execution_order(scene: NodeScene) -> list[NodeInstance]:
        in_degree = {uid: 0 for uid in scene.graph.all_nodes.keys()}
        adjacency = {uid: [] for uid in scene.graph.all_nodes.keys()}

        for conn in scene.graph.all_connections.values():
            node_id = conn.from_slot.node_id
            target_node_id = conn.to_slot.node_id
            if target_node_id not in adjacency[node_id]:
                adjacency[node_id].append(target_node_id)
            
            in_degree[target_node_id] += 1

        queue = deque([uid for uid, deg in in_degree.items() if deg == 0])
        order: list[NodeInstance] = []

        while queue:
            current_id = queue.popleft()
            order.append(scene.graph.all_nodes[current_id])
            
            for dependent_node in adjacency[current_id]:
                in_degree[dependent_node] -= 1
                if in_degree[dependent_node] == 0:
                    queue.append(dependent_node)

        if len(order) != len(scene.graph.all_nodes):
            # TODO: trocar por uma exceção customizada
            raise Exception("Connection Recursion detected")

        return order
