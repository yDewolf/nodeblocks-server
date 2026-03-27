from nodeserver.api.base_nodes import BaseNode
from nodeserver.networking.nodes.node.base_nodes import NodeMirror


# Responsável por converter um mirror em algum tipo de "Node Lógico"
class BaseNodeBuilder:
    # Método principal do builder
    # Constrói "qualquer tipo" de Node, baseado no mirror
    def build_node(self, mirror: NodeMirror) -> BaseNode:
        node = BaseNode(mirror)
        return node


# Example
class ExampleNode(BaseNode):
    operation: str = ""
    def __init__(self, mirror: NodeMirror | None = None):
        super().__init__(mirror)
        if not mirror:
            return

    def forward(self, input):
        if not type(input) is list[float] and not type(input) is list[int]:
            return
        
        if len(input) < 2:
            return

        match self.operation:
            case "+": return sum(input)
            case "-": return input[0] - input[1]
            case "/": return input[0] / input[1]
            case "*": return input[0] * input[1]


class NodeBuilder(BaseNodeBuilder):
    def build_node(self, mirror: NodeMirror) -> BaseNode:
        node = ExampleNode(mirror)
        match mirror.type_name:
            case "SumNode":
                node.operation = "+"
            
            case "SubNode":
                node.operation = "-"

            case "MulNode":
                node.operation = "*"

            case "DivNode":
                node.operation = "/"
            
            case _:
                node.operation = "unknown"
  
        return node