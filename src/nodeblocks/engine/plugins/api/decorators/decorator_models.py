from typing import Optional, Union

from nodeblocks.engine.plugins.api.plugin import Plugin
from nodeblocks.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers
from nodeblocks.protocols.manifest.base_manifest import DataModel

class PluginDefModel(DataModel):
    # TODO: if target plugin is None, then compiler will use the current plugin
    target_plugin: Optional[type[Plugin]] = None


class PluginNodeDefModel(PluginDefModel):
    id: str

# TODO: talvez incluir um metadata base aqui
class PluginDataTypeDefModel(PluginDefModel):
    id: str
    cls_name: str
    alias_class_paths: list[str] = []

    base_id: DefaultDataTypes
    renderer: DefaultRenderers
    whitelist: list[str]

PluginDecoDefModels = Union[
    PluginNodeDefModel, PluginDataTypeDefModel
]