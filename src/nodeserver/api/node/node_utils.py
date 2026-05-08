import os
import types
from typing import Annotated, Any, Type, get_args, get_origin

from pydantic import BaseModel

from nodeserver.api.node.slots import InputSlotIO, NodeSlot, OutputSlotIO, SlotConfig, _SlotIO
from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror

class NodeUtils:
    @staticmethod
    def make_state_file_path(mirror: NodeMirror, root_path: str, extension: str) -> tuple[str, str]:
        filename = f"{mirror.uid}.{extension}"
        return os.path.join(root_path, filename), filename

    @staticmethod
    def process_model(model: Type[BaseModel], default_is_input: bool, generatedSlots: Type, _slot_definitions: dict[str, Any]):
        for name, field in model.model_fields.items():
            slot_class = NodeSlot
            max_inputs: int = 1
            is_input = default_is_input
            extra_args = {}

            for meta in field.metadata:
                if isinstance(meta, SlotConfig):
                    if meta.slot_class: slot_class = meta.slot_class
                    is_input = meta.is_input
                    extra_args = meta.extra_kwargs
                    max_inputs = meta.max_inputs

            raw_type = field.annotation

            io_generic = InputSlotIO[raw_type] if is_input else OutputSlotIO[raw_type]
            _slot_definitions[name] = {
                "class": slot_class,
                "io": io_generic,
                "args": extra_args,
                "max_inputs": max_inputs,
                "raw_type": raw_type
            }
            
            generatedSlots.__annotations__[name] = slot_class[io_generic] # type: ignore
    