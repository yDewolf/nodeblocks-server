from typing import Any, Sequence

from nodeserver.engine.plugins.api.decorators.plugin_decorators import plugin_datatype
from nodeserver.engine.plugins.api.plugin_datatype import PluginDatatype
from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers


@plugin_datatype(
    id="float",
    base_id=DefaultDataTypes.FLOAT,
    default_renderer=DefaultRenderers.SCALAR,
    aliases=[float]
)
class FloatDataType(PluginDatatype, float):
    def serialize(self): return self


@plugin_datatype(
    id="int",
    base_id=DefaultDataTypes.INT,
    default_renderer=DefaultRenderers.SCALAR,
    aliases=[int]
)
class IntDataType(PluginDatatype, int):
    def serialize(self): return self


@plugin_datatype(
    id="uint",
    base_id=DefaultDataTypes.UINT,
    default_renderer=DefaultRenderers.SCALAR,
)
class UIntDataType(PluginDatatype, int):
    def serialize(self):
        # TODO: pensar em um jeito melhor de implementar UINT lol
        return max(0, self)


@plugin_datatype(
    id="bool",
    base_id=DefaultDataTypes.BOOLEAN,
    default_renderer=DefaultRenderers.SCALAR,
    aliases=[bool]
)
class BoolDataType(PluginDatatype):
    # TODO: melhorar isso aqui tbm
    value: bool
    def serialize(self): return self

@plugin_datatype(
    id="array",
    base_id=DefaultDataTypes.ARRAY,
    default_renderer=DefaultRenderers.ARRAY,
    aliases=[list, tuple]
)
class ArrayDataType(PluginDatatype, Sequence):
    def serialize(self): return self


@plugin_datatype(
    id="string",
    base_id=DefaultDataTypes.TEXT,
    default_renderer=DefaultRenderers.TEXT,
    aliases=[str]
)
class StringDataType(PluginDatatype, str):
    def serialize(self): return self


@plugin_datatype(
    id="unknown",
    base_id=DefaultDataTypes.UNKNOWN,
    default_renderer=DefaultRenderers.NOT_IMPLEMENTED,
)
class UnknownDataType(PluginDatatype):
    def serialize(self): return self

