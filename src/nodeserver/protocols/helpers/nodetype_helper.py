from nodeserver.protocols.manifest.node.datatypes import ParameterSpec
from nodeserver.protocols.manifest.node.node_manifest import NodeSlotSpec, NodeTypeSpec


class NodeTypeHelper:
    @staticmethod
    def create_spec(namespace: str, id: str, parameters: dict[str, ParameterSpec], slots: dict[str, NodeSlotSpec]) -> NodeTypeSpec:
        return NodeTypeSpec(
            namespace=namespace,
            id=id,
            parameters=parameters,
            slots=slots
        )
