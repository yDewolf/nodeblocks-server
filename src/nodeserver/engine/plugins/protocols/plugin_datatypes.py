from nodeserver.engine.exceptions.plugin_exceptions import MissingNamespacePluginDataType
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec

from typing import Optional

# FIXME: quando for fazer model dump json, enviar apenas class_path e as coisas do namespace
class PluginDatatypeSpec(DataTypeSpec):
    """Maps a python class to a DataTypeSpec Fully Qualified Name (fqn) through import string."""
    namespace: Optional[str] = None # Must be autofilled by the PluginCompiler

    class_path: str # ex: "myplugin.types.ImageBuffer"

    @property
    def fqn(self):
        if self.namespace is None:
            raise MissingNamespacePluginDataType(self.id, self.class_path)

        return super().fqn
