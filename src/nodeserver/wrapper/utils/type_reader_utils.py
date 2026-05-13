
from typing import Callable

from nodeserver.api.node.nodes import BaseNode
from nodeserver.wrapper.nodes.data.node_data import NodeData
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import SlotData
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import ConstructorModel, TypeFileReader
from nodeserver.wrapper.nodes.helpers.node_constructor import BaseMirrorConstructor, CustomMirrorConstructor
from nodeserver.wrapper.nodes.node.base_nodes import _ParsedNode, NodeMirror


class TypeReaderUtils:
    @staticmethod
    def make_constructors(base_types: TypeFileReader, default_slots: dict[str, SlotData], default_builder: Callable[[NodeMirror], _ParsedNode], models: list[ConstructorModel]) -> list[BaseMirrorConstructor]:
        constructors: list[BaseMirrorConstructor] = []
        for model in models:
            constructor = CustomMirrorConstructor(
                type_name=model.type_name,
                data=model.node_data if model.node_data else NodeData({}),
                slot_types=base_types.slot_types,
                slots=model.slots if model.slots else default_slots,
                builder_func=model.parser if model.parser else default_builder,
            )
            constructors.append(constructor)

        return constructors
    
    @staticmethod
    def make_types_from_registry(types_version: int, types_id: str, node_registry: dict[str, type[BaseNode]]):
        types = TypeFileReader.new(types_version, types_id, {}, [])
        TypeReaderUtils.set_types_from_registry(types, node_registry)
        return types
    
    @staticmethod
    def set_types_from_registry(types: TypeFileReader, node_registry: dict[str, type[BaseNode]]):
        node_constructors: list[ConstructorModel] = []
        slot_types = {}
        for type_name, node_type in node_registry.items():
            super_slot_types, constructor = node_type.generate_types(slot_types, type_name)
            node_constructors.append(constructor)
            slot_types = super_slot_types

        def auto_parser(mirror: NodeMirror) -> _ParsedNode:
            node_class = node_registry.get(mirror.type_name, None)
            if not node_class:
                raise Exception(f"Couldn't parse node with type {mirror.type_name}")

            return node_class(mirror)

        types.slot_types.update(slot_types)
        types.set_new_constructors(TypeReaderUtils.make_constructors(
            types, {}, auto_parser, node_constructors
        ))

        return types