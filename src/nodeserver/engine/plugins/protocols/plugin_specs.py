from pydantic import BaseModel
from nodeserver.engine.exceptions.plugin.plugin_exceptions import MissingNamespacePluginDataType
from typing import Optional, Self
from nodeserver.protocols.manifest.base_manifest import NamespaceModel
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec

# These are internal plugin system specs

# Datatype Stuff

class PluginDatatypeRef(NamespaceModel):
    class_path: str


class PluginDatatypeSpec(DataTypeSpec, PluginDatatypeRef):
    """Maps a python class to a DataTypeSpec Fully Qualified Name (fqn) through import string."""
    namespace: Optional[str] = None # Must be autofilled by the PluginCompiler

    @classmethod
    def from_ref_and_spec(cls, ref: PluginDatatypeRef, spec: DataTypeSpec) -> Self:
        return cls(
            namespace=ref.namespace,
            id=ref.id,
            class_path=ref.class_path,
            base_id=spec.base_id,
            default_renderer=spec.default_renderer,
            whitelist=spec.whitelist
        )

    @property
    def fqn(self):
        if self.namespace is None:
            raise MissingNamespacePluginDataType(self.id, self.class_path)

        return super().fqn

    def to_plugin_datatype_ref(self) -> PluginDatatypeRef:
        if self.namespace is None:
            raise MissingNamespacePluginDataType(self.id, self.class_path)

        return PluginDatatypeRef(
            namespace=self.namespace,
            id=self.id,
            class_path=self.class_path
        )

# NodeType stuff

class NodeCacheEntry(BaseModel):
    class_path: str
    required_datatypes: list[str] # datatype fqn list
