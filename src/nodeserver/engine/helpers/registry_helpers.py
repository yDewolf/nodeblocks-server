import inspect

from pydantic import BaseModel
from nodeserver.engine.helpers.logic_node_helper import LogicNodeHelper
from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.protocols.manifest.node.node_manifest import NodeTypeSpec


class NodeTypeRegistryHelper:
    @staticmethod
    def generate_spec(namespace: str, id: str, node_class: type[BaseNode]) -> NodeTypeSpec:
        inputs = LogicNodeHelper._generate_specs_for_slots(node_class.InputModel, True)
        outputs = LogicNodeHelper._generate_specs_for_slots(node_class.OutputModel, False)
        slot_specs = {**inputs, **outputs}

        return NodeTypeSpec(
            namespace=namespace,
            id=id,
            parameters=TODO,
            slots=slot_specs
        )
