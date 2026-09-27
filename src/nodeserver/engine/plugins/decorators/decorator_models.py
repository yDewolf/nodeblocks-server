from typing import Optional, Union

from nodeserver.engine.plugins.plugin import Plugin
from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers
from nodeserver.protocols.manifest.base_manifest import DataModel

class PluginDefModel(DataModel):
    # TODO: if target plugin is None, then compiler will use the current plugin
    target_plugin: Optional[type[Plugin]] = None


class PluginNodeDefModel(PluginDefModel):
    id: str

class PluginDataTypeDefModel(PluginDefModel):
    id: str
    cls_name: str

    base_id: DefaultDataTypes
    renderer: DefaultRenderers
    whitelist: list[str]

PluginDecoDefModels = Union[
    PluginNodeDefModel, PluginDataTypeDefModel
]