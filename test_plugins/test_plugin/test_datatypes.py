from nodeserver.engine.plugins.plugin_decorators import plugin_datatype
from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers


@plugin_datatype(
    id="test_datatype",
    base_id=DefaultDataTypes.TEXT,
    default_renderer=DefaultRenderers.TEXT
)
class TestDatatype:
    pass
