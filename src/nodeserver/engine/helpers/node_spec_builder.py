from types import NoneType
from typing import Annotated, Any, Optional, Union, get_args, get_origin

from pydantic.fields import FieldInfo

from nodeserver.engine.protocols.node.logic_nodes import BaseNode, NodeIO
from nodeserver.engine.protocols.parameters.node_parameter import NodeParameters, ParamArguments
from nodeserver.engine.protocols.spec_dataclasses import SlotSpecMeta
from nodeserver.engine.registry.type_registry import TypeRegistry
from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec, ParameterSpec, ParameterSpecAdapter
from nodeserver.protocols.manifest.node.node_manifest import NodeSlotSpec, NodeTypeSpec

class NodeSpecBuilder:
    CORE_UNKNOWN_FQN = "core:unknown"

    def __init__(self, registry: TypeRegistry) -> None:
        self.registry = registry

    def build_node_spec(self, namespace: str, id: str, node_cls: type[BaseNode]) -> NodeTypeSpec:
        inputs = self._generate_specs_for_slots(node_cls.Inputs, is_input=True)
        outputs = self._generate_specs_for_slots(node_cls.Outputs, is_input=False)
        parameters = self._generate_specs_for_parameters(node_cls.Parameters)

        return NodeTypeSpec(
            namespace=namespace,
            id=id,
            slots={**inputs, **outputs},
            parameters=parameters
        )


    def _generate_specs_for_slots(self, slot_model_cls: type[NodeIO], is_input: bool) -> dict[str, NodeSlotSpec]:
        slot_specs: dict[str, NodeSlotSpec] = {}
        for field_name, field_info in slot_model_cls.model_fields.items():
            meta, is_default = self._extract_slot_meta(field_info)
            datatype_spec: Optional[DataTypeSpec] = None

            # get defined datatype using slot meta
            if not is_default and meta.datatype:
                datatype_fqn: str = meta.datatype.fqn if isinstance(meta.datatype, DataTypeSpec) else meta.datatype
                # Even if a spec already exists in metadata, it is safer to get it
                # from the registry itself
                datatype_spec = self.registry.get_datatype_spec(datatype_fqn)

            # if not found, get datatype using field annotation
            if not datatype_spec:
                datatype_spec = self._infer_datatype_from_type(field_info.annotation)

            # if none was found, use default unknown datatype spec
            if not datatype_spec:
                datatype_spec = self.registry.get_datatype_spec(self.CORE_UNKNOWN_FQN)

            is_collection = get_origin(field_info.annotation) is list
            max_connections: int = (
                meta.max_connections if meta.max_connections is not None
                else (0 if (is_collection or not is_input) else 1)
            )

            slot_specs[field_name] = NodeSlotSpec(
                is_input=is_input,
                data_type_id=datatype_spec.fqn,
                max_connections=max_connections,
                required=meta.required,
            )

        return slot_specs

    def _generate_specs_for_parameters(self, param_model_cls: type[NodeParameters]) -> dict[str, ParameterSpec]:
        param_specs: dict[str, ParameterSpec] = {}

        for field_name, field_info in param_model_cls.model_fields.items():
            args = ParamArguments.model_validate(field_info.json_schema_extra) if field_info.json_schema_extra else ParamArguments(datatype_fqn=self.CORE_UNKNOWN_FQN)
            datatype_spec: Optional[DataTypeSpec] = None

            # get defined spec using args
            if args.datatype_fqn and args.datatype_fqn != self.CORE_UNKNOWN_FQN:
                datatype_spec = self.registry.get_datatype_spec(args.datatype_fqn)

            # if not found, get datatype using field annotation
            if not datatype_spec:
                datatype_spec = self._infer_datatype_from_type(field_info.annotation)

            # if none was found, use default unknown datatype spec
            if not datatype_spec:
                datatype_spec = self.registry.get_datatype_spec(self.CORE_UNKNOWN_FQN)

            base_type = datatype_spec.base_id
            if args.options is not None: base_type = DefaultDataTypes.OPTIONS

            spec_data = {
                "type": base_type,
                # "label": field_info.title or field_name,
                "default": field_info.default if not field_info.is_required() else None,
                "required": field_info.is_required(),
                "datatype_fqn": datatype_spec.fqn,
                **args.model_dump(exclude_none=True),
            }

            param_specs[field_name] = ParameterSpecAdapter.validate_python(spec_data)

        return param_specs


    # Utils:
    
    def _infer_datatype_from_type(self, annotation: Any) -> Optional[DataTypeSpec]:
        if annotation is None or annotation is NoneType:
            return None

        origin = get_origin(annotation)
        if origin is Annotated:
            args = get_args(annotation)
            if args:
                return self._infer_datatype_from_type(args[0])

        if origin is Union:
            non_none_args = [arg for arg in get_args(annotation) if arg is not NoneType]
            if non_none_args:
                return self._infer_datatype_from_type(non_none_args[0])
            return None

        if origin is list:
            args = get_args(annotation)
            if len(args) == 0:
                raise Exception(f"Invalid datatype annotation ({annotation}) format. List types must specify a type using list[<type>]")

            return self._infer_datatype_from_type(args[0])

        return self.registry.get_datatype_by_annotation(annotation)
    
    @classmethod
    def _extract_slot_meta(cls, field_info: FieldInfo) -> tuple[SlotSpecMeta, bool]:
        for meta in field_info.metadata:
            if isinstance(meta, SlotSpecMeta):
                return meta, False

        return SlotSpecMeta(datatype=cls.CORE_UNKNOWN_FQN), True
