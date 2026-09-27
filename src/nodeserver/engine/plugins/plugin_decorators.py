from typing import Any, Optional, Type, Union

from nodeserver.engine.exceptions.plugin_exceptions import InvalidPluginDecoratorUsage
from nodeserver.engine.protocols.node.logic_nodes import BaseNode
from nodeserver.protocols.enums.datatype_enums import DefaultDataTypes, DefaultRenderers
from nodeserver.protocols.manifest.base_manifest import DataModel


class PluginNodeDefModel(DataModel):
    id: str


def plugin_node(id: Optional[str] = None):
    """Registers a BaseNode in the current Plugin"""
    def wrapper(cls: Type) -> Type:
        if not issubclass(cls, BaseNode):
            raise InvalidPluginDecoratorUsage(cls, plugin_node)

        node_id = id or cls.__name__
        node_meta = PluginNodeDefModel(id=node_id)

        setattr(cls, "__plugin_node_meta__", node_meta)
        return cls

    return wrapper


class PluginDataTypeDefModel(DataModel):
    id: str
    cls_name: str

    base_id: DefaultDataTypes
    renderer: DefaultRenderers
    whitelist: list[str]

def plugin_datatype(id: str, base_id: DefaultDataTypes, default_renderer: DefaultRenderers, whitelist: Optional[list[str]] = None):
    """Registers a DataType in the current Plugin"""
    def wrapper(cls: Type) -> Type:
        datatype_meta = PluginDataTypeDefModel(
            id=id,
            cls_name=cls.__name__,
            base_id=base_id,
            renderer=default_renderer,
            whitelist=whitelist or [base_id],
        )
        setattr(cls, "__plugin_datatype_meta__", datatype_meta)
        return cls
    
    return wrapper


def get_plugin_meta(attr: Any) -> Optional[Union[PluginNodeDefModel, PluginDataTypeDefModel]]:
    if not isinstance(attr, type):
        return None
    
    if hasattr(attr, "__plugin_node_meta__"):
        return attr.__plugin_node_meta__

    if hasattr(attr, "__plugin_datatype_meta__"):
        return attr.__plugin_datatype_meta__
        
    return None
