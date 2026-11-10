from typing import Any

from nodeblocks.engine.plugins.api.decorators.plugin_decorators import plugin_datatype
from nodeblocks.engine.plugins.api.plugin_datatype import PluginDatatype
from nodeblocks.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers
from nodeblocks.protocols.manifest.node.datatype_value_meta import NoMetaDataTypeValue, SerializedDataTypeValue


@plugin_datatype(
    id="test_datatype",
    base_id=DefaultDataTypes.TEXT,
    default_renderer=DefaultRenderers.TEXT
)
class TestDatatype(PluginDatatype):
    value: float

    def __init__(self, value: float) -> None:
        super().__init__()
        self.value = value
    
    def serialize(self) -> SerializedDataTypeValue:
        return self.serialize_value(self.value)

    @classmethod
    def serialize_value(cls, value: Any) -> SerializedDataTypeValue:
        return NoMetaDataTypeValue(value=value)
