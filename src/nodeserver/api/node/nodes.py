from abc import abstractmethod
import json
import logging
import os
import pathlib
from typing import Annotated, Any, Optional, Type, get_args, get_origin, get_type_hints

from pydantic import BaseModel

from nodeserver.api.internal.instance_state import InternalNodeState
from nodeserver.api.node.node_parameters import ParamConfig
from nodeserver.api.node.node_utils import NodeUtils
from nodeserver.api.node.slots import Input, NodeSlot, SlotConfig, _SlotIO
from nodeserver.wrapper.nodes.data.node_data import NodeData
from nodeserver.wrapper.nodes.data.node_data_types import UNKNOWN_TYPE, BaseSlotType, DataTypeUtils, SuperSlotTypes
from nodeserver.wrapper.nodes.helpers.connection_manager import ConnectionManager
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import NodeParameterData, NodeParameterDataAdapter, SlotData
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import ConstructorModel
from nodeserver.wrapper.nodes.helpers.node_manager import NodeMirrorManager
from nodeserver.wrapper.nodes.node.base_nodes import _ParsedNode, NodeMirror, SlotMirror

logger = logging.getLogger("nds.nodes")

class _Node[inputType: BaseModel, outputType: BaseModel](_ParsedNode):
    _version: int = 0

    dirty: bool = True
    bypass_cache: bool = False
    
    class _Slots: pass
    # Parsed Slots
    class Slots(_Slots): pass

    _slots: Slots

    class Parameters(BaseModel):
        pass

    _parameters: Parameters
    _params_spec: dict[str, dict]

    def __init__(self, mirror: NodeMirror | None = None):
        super().__init__(mirror)
        self._parameters = self.Parameters()
        self._slots = self.Slots()
        self._build_slots()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._params_spec = {}
        if not hasattr(cls, "Parameters") or not cls.Parameters is not BaseModel:
            return
        
        for name, field in cls.Parameters.model_fields.items():
            param_info = {
                "type": DataTypeUtils._match_super_type(field.annotation.__name__ if field.annotation else ""),
                "default": field.default,
                "label": name.replace("_", " ").title(),
                # "widget": "number"
            }

            for meta in field.metadata:
                if isinstance(meta, ParamConfig):
                    param_info.update(meta.dump())
            
            cls._params_spec[name] = param_info


    def _build_slots(self):
        hints = get_type_hints(self._Slots, globalns=globals())
        self._slots = self._Slots()
        for attribute_name, hint in hints.items():
            slot_mirror: Optional[SlotMirror] = None
            if self.has_mirror():
                slot_mirror = self._mirror.get_slot(attribute_name)
            
            slot_instance = self._build_slot_instance(hint, slot_mirror)
            setattr(self._slots, attribute_name, slot_instance)

    @staticmethod
    def _build_slot_instance(hint: type[NodeSlot], slot_mirror: Optional[SlotMirror]):
        origin = get_origin(hint) or hint
        args = get_args(hint)

        actual_io = args[0] if args else _SlotIO
        return origin(mirror=slot_mirror, output_cls=actual_io)

    def slot(self, name: str) -> NodeSlot:
        slot = getattr(self._slots, name)
        if not isinstance(slot, NodeSlot):
            raise Exception(f"Tried to access an attribute ({name} in {self.__class__}) that is not a NodeSlot")
        
        if slot == None:
            raise Exception(f"Slot with name '{name}' doesn't exist for node ({self.__class__})")
        
        return slot


    def _ensure_parameters_updated(self):
        for name, param in self._mirror.data.parameters.items():
            if not hasattr(param, name):
                raise Exception(f"Parameter {name} from node {self._mirror} doesn't exist in instance {self}")

            setattr(self._parameters, name, param.value)

    @abstractmethod
    def _parse_inputs(self, raw_inputs: dict):
        pass

    @abstractmethod
    def pre_forward(self, input: inputType):
        pass

    @abstractmethod
    def forward(self, input: inputType) -> outputType:
        pass

    @abstractmethod
    def post_forward(self):
        pass


    @abstractmethod
    def self_validate(self, node_manager: NodeMirrorManager, conn_manager: ConnectionManager) -> bool:
        return True

    # Override these on your Node class:
    # Your load state logic
    @abstractmethod
    def load_state(self, root_state_path: str, state: InternalNodeState):
        if state.relative_state_path:
            my_state_file_path = os.path.join(root_state_path, state.relative_state_path)
            print(my_state_file_path)
            # Open file and load stuff


    # Should have save logic
    @abstractmethod
    def save_state(self, root_state_path: str) -> Optional[InternalNodeState]:
        state = self.get_state()
        if state:
            my_state_file_path, filename = NodeUtils.make_state_file_path(self._mirror, root_state_path, "json")
            state.relative_state_path = str(pathlib.Path(my_state_file_path).relative_to(root_state_path))
            
            with open(my_state_file_path, "w") as file:
                file.write(json.dumps({"some": "data"}))

        # Do some Save stuff if you need to
        return state

    # Shouldn't have save logic
    @abstractmethod
    def get_state(self) -> Optional[InternalNodeState]:
        return InternalNodeState(
            relative_state_path=None,
            state_data=None
        )


    def get_execution_hash(self, output_cache: dict[SlotMirror, _SlotIO]) -> int:
        input_versions = 0
        slots_version = 0
        for slot in self._mirror.slots.get(SuperSlotTypes.INPUT, []):
            slots_version += slot._version
            for conn in slot.connections:
                cached = output_cache.get(conn)
                if cached: input_versions += cached._version
        
        return (self._version + self._mirror.data._version + input_versions + slots_version)

    def resolve_inputs(self, output_cache: dict) -> dict:
        raw_inputs = {}
        for slot in self._mirror.slots.get(SuperSlotTypes.INPUT, []):
            values = [output_cache[conn].value for conn in slot.connections if conn in output_cache]
            if not values: raw_inputs[slot.slot_name] = None

            real_slot = self.slot(slot.slot_name)
            if real_slot._io.is_collection():
                raw_inputs[slot.slot_name] = values[:real_slot._io._max_inputs]
                if len(values) > real_slot._io._max_inputs:
                    logger.warning(f"WARNING: Shrinking node inputs for slot {slot}")
                
                continue

            raw_inputs[slot.slot_name] = values[0]
        
        return raw_inputs


    @classmethod
    def generate_types(cls, super_slot_types: dict[str, BaseSlotType] = {}) -> tuple[dict[str, BaseSlotType], ConstructorModel]:
        super_types: dict[str, BaseSlotType] = super_slot_types
        slot_types: dict[str, SlotData] = {}
        
        cls._add_cls_slot_types(super_types, slot_types)
        constructor = cls._generate_constructor(slot_types)
        return (super_types, constructor)

    @classmethod
    def _generate_constructor(cls, slot_types: dict[str, SlotData]) -> ConstructorModel:
        param_data: dict[str, NodeParameterData] = {}
        for param_name, spec in cls._params_spec.items():
            param_data[param_name] = NodeParameterDataAdapter.validate_python(spec)

        constructor: ConstructorModel = ConstructorModel(
            type_name=str(cls.__name__),
            node_data=NodeData(param_data),
            slots=slot_types,
            parser=None,
        )

        return constructor

    @classmethod
    def _add_cls_slot_types(cls, super_types: dict[str, BaseSlotType], slot_types: dict[str, SlotData]):
        slot_hints = get_type_hints(cls.Slots, globalns=globals())
        for attribute_name, hint in slot_hints.items():
            slot_instance = cls._build_slot_instance(hint, None)
            cls._add_slot_types(attribute_name, slot_instance, super_types, slot_types)

    @classmethod
    def _add_slot_types(cls, key: str, slot_instance: NodeSlot, super_types: dict[str, BaseSlotType], slot_types: dict[str, SlotData]):
        # FIXME: Improve DataTypes so it can make new DataTypes and pass it with the scene
        raw_type = slot_instance._io.get_type()

        data_type = slot_instance._io._datatype_override
        if not data_type:
            data_type = DataTypeUtils._match_data_type_str(raw_type.__name__)
        
        super_slot_name = f"{slot_instance.__class__.__name__}:{raw_type.__name__}:{"input" if slot_instance._io._is_input else "output"}"
        if not super_types.__contains__(super_slot_name):
            super_types[super_slot_name] = BaseSlotType(
                type_name=super_slot_name, 
                super_type=SuperSlotTypes.INPUT if slot_instance._io._is_input else SuperSlotTypes.OUTPUT,
                data_type=data_type,
                type_whitelist=[SuperSlotTypes.OUTPUT if slot_instance._io._is_input else SuperSlotTypes.INPUT], # type: ignore
                name_whitelist=[super_slot_name]
            )
        
        slot_types[key] = SlotData(
            type=super_slot_name,
            data_type=DataTypeUtils._match_super_type(raw_type.__name__)
        )

class NoInput(BaseModel):
    pass

class NoOutput(BaseModel):
    pass

class BaseNode[inputType: BaseModel, outputType: BaseModel](_Node[inputType, outputType]):
    InputModel: Type[BaseModel] = NoInput
    OutputModel: Type[BaseModel] = NoOutput
    _slot_definitions: dict[str, Any]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        class GeneratedSlots:
            pass
        
        cls._slot_definitions = {}
        NodeUtils.process_model(cls.InputModel, default_is_input=True, slots_class=GeneratedSlots, _slot_definitions=cls._slot_definitions)
        NodeUtils.process_model(cls.OutputModel, default_is_input=False, slots_class=GeneratedSlots, _slot_definitions=cls._slot_definitions)
        
        cls._Slots = cls.Slots
        cls.Slots = GeneratedSlots # type: ignore
    
    def _build_slots(self):
        super()._build_slots()
        for name, spec in self._slot_definitions.items():
            slot_mirror: Optional[SlotMirror] = None
            if self.has_mirror():
                slot_mirror = self._mirror.get_slot(name)
                if not slot_mirror: continue

            instance: NodeSlot = self._build_slot_instance_from_spec(spec, slot_mirror)

            setattr(self._slots, name, instance)
    
    @classmethod
    def _build_slot_instance_from_spec(cls, spec: dict, slot_mirror: Optional[SlotMirror]):
        instance: NodeSlot = spec["class"](
            mirror=slot_mirror, 
            output_cls=spec["io"],
            **spec["args"]
        )

        instance._io._max_inputs = spec["max_inputs"]
        instance._io._raw_io_type = spec["raw_type"]
        datatype_override = spec.get("datatype_override")
        instance._io._datatype_override = datatype_override
        if datatype_override and instance.has_mirror():
            instance._mirror.data_type = datatype_override

        return instance

    @classmethod
    def _add_cls_slot_types(cls, super_types: dict[str, BaseSlotType], slot_types: dict[str, SlotData]):
        for name, spec in cls._slot_definitions.items():
            slot_instance = cls._build_slot_instance_from_spec(spec, None)
            cls._add_slot_types(name, slot_instance, super_types, slot_types)

    def _parse_inputs(self, raw_input_data: dict) -> BaseModel:
        return self.InputModel(**raw_input_data)

    @abstractmethod
    def forward(self, input_data: inputType) -> outputType:
        pass
