
from typing import Optional

from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec


class DatatypeHelper:
    @staticmethod
    def create_spec(base_id: DefaultDataTypes, renderer: DefaultRenderers, whitelist: Optional[list[str]] = None) -> DataTypeSpec:
        return DataTypeSpec(
            base_id=base_id,
            default_renderer=renderer,
            whitelist=whitelist or [base_id]
        )

    @staticmethod
    def are_types_compatible(source_spec: DataTypeSpec, target_spec: DataTypeSpec) -> bool:
        # será que em algum momento vai existir um datatype que não é compatível consigo mesmo??
        if source_spec.id == source_spec.id:
            return True
        
        if source_spec.id and source_spec.id in target_spec.whitelist:
            return True

        return source_spec.base_id in target_spec.whitelist
