import os
from typing import Any, Optional, Type

from pydantic import BaseModel

from nodeserver.api.node.abstract._slots import _SlotIO
from nodeserver.api.node.slots import InputSlotIO, NodeSlot, OutputSlotIO, SlotConfig
from nodeserver.wrapper.nodes.data.node_data_types import DefaultDataTypes
from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror

class NodeUtils:
    @staticmethod
    def make_state_file_path(mirror: NodeMirror, root_path: str, extension: str) -> tuple[str, str]:
        filename = f"{mirror.uid}.{extension}"
        return os.path.join(root_path, filename), filename

    @staticmethod
    def process_model(model: Type[BaseModel], default_is_input: bool, slots_class: Type, _slot_definitions: dict[str, Any]):
        for name, field in model.model_fields.items():
            slot_class = NodeSlot
            slot_io = _SlotIO

            max_inputs: Optional[int] = None
            renderer_override: Optional[DefaultDataTypes] = None
            is_input = default_is_input
            extra_args = {}

            for meta in field.metadata:
                if isinstance(meta, SlotConfig):
                    if meta.slot_class: slot_class = meta.slot_class
                    if meta.slot_io: slot_io = meta.slot_io

                    is_input = meta.is_input
                    extra_args = meta.extra_kwargs
                    max_inputs = meta.max_inputs
                    renderer_override = meta.renderer_override

            raw_type = field.annotation

            io_generic = slot_io[raw_type, is_input]
            _slot_definitions[name] = {
                "class": slot_class,
                "io": io_generic,
                "args": extra_args,
                "max_inputs": max_inputs,
                "raw_type": raw_type,
                "renderer_override": renderer_override
            }
            
            slots_class.__annotations__[name] = slot_class[io_generic] # type: ignore
    