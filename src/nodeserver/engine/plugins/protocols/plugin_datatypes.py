from pydantic import model_validator

from nodeserver.engine.exceptions.plugin_exceptions import MissingNamespacePluginDataType
from nodeserver.protocols.manifest.base_manifest import make_namespace_fqn


from typing import Optional

from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec

class PluginDatatypeSpec(DataTypeSpec):
    """Maps a python class to a DataTypeSpec Fully Qualified Name (fqn) through import string."""
    namespace: Optional[str] = None # Must be autofilled by the PluginCompiler

    class_path: str # ex: "myplugin.types.ImageBuffer"

    @property
    def fqn(self):
        if self.namespace is None:
            raise MissingNamespacePluginDataType(self.id, self.class_path)

        return super().fqn
