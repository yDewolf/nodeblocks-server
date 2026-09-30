from nodeserver.engine.plugins.api.decorators.plugin_decorators import plugin_datatype
from nodeserver.engine.plugins.api.plugin_datatype import PluginDatatype
from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers


@plugin_datatype(
    id="test_datatype",
    base_id=DefaultDataTypes.TEXT,
    default_renderer=DefaultRenderers.TEXT
)
class TestDatatype(PluginDatatype):
    value: float
    def serialize(self) -> dict | str | bool | int | float | list | tuple | None:
        return self.value
