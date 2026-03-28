from collections import deque

from nodeserver.api.base_nodes import BaseNode
from nodeserver.networking.nodes.data.node_data_types import SuperSlotTypes
from nodeserver.networking.nodes.node.base_nodes import NodeMirror

class NodeUtils:
    @staticmethod
    def get_node_execution_order(nodes: list[BaseNode]) -> list[NodeMirror]:
        execution_order = NodeUtils._get_node_execution_order([node._mirror for node in nodes])
        return execution_order

    # Obrigado Gemini por fazer esse algoritmo aí, tamo junto
    @staticmethod
    def _get_node_execution_order(nodes: list[NodeMirror]) -> list[NodeMirror]:
        in_degree: dict[NodeMirror, int] = {node: 0 for node in nodes}
        adjacency: dict[NodeMirror, list[NodeMirror]] = {node: [] for node in nodes}

        for node in nodes:
            output_slots = node.slots.get(SuperSlotTypes.OUTPUT, [])
            
            for slot in output_slots:
                for target_slot, connection in slot.connections.items():
                    target_node = target_slot.parent_node
                    
                    if target_node in in_degree:
                        in_degree[target_node] += 1
                        adjacency[node].append(target_node)

        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        execution_order: list[NodeMirror] = []

        while queue:
            current_node = queue.popleft()
            execution_order.append(current_node)

            for dependent_node in adjacency[current_node]:
                in_degree[dependent_node] -= 1
                
                if in_degree[dependent_node] == 0:
                    queue.append(dependent_node)

        if len(execution_order) != len(nodes):
            # Recursion Error
            return []

        return execution_order