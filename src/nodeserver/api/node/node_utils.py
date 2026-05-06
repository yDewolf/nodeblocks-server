import os
from typing import Annotated, Any, Type, get_args, get_origin

from pydantic import BaseModel

from nodeserver.api.node.slots import NodeSlot, SlotConfig, SlotIO
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
            is_input = default_is_input
            extra_args = {}

            if get_origin(field.annotation) is Annotated:
                metadata = get_args(field.annotation)
                for meta in metadata:
                    if isinstance(meta, SlotConfig):
                        if meta.slot_class: slot_class = meta.slot_class
                        is_input = meta.is_input
                        extra_args = meta.extra_kwargs
            
            raw_type = field.annotation
            if get_origin(raw_type) is Annotated:
                raw_type = get_args(raw_type)[0]

            io_type = SlotIO[raw_type, None] if is_input else SlotIO[None, raw_type]
            _slot_definitions[name] = {
                "class": slot_class,
                "io": io_type,
                "args": extra_args
            }
            
            generatedSlots.__annotations__[name] = slot_class[io_type]
