from pathlib import Path

from nodeserver.engine.metadata.plugin_metadata import PluginMetadataGenerator
from nodeserver.engine.plugins.plugin_spec_manager import PluginSpecManager
from nodeserver.protocols.helpers.metadata.metadata_utils import METADATA_FOLDER_NAME, _MetadataLoad, MetadataFileUtils
from nodeserver.protocols.manifest.metadata.metadata_header import Metadata, MetadataManifest
from nodeserver.server.protocols.providers.metadata_provider_protocol import IMetadataProvider


class FileMetadataProvider(IMetadataProvider):
    plugins_folder: Path
    plugin_manager: PluginSpecManager
    metadata_gen: PluginMetadataGenerator
    
    def __init__(self, plugins_folder: Path, plugin_manager: PluginSpecManager) -> None:
        super().__init__()
        self.plugins_folder = plugins_folder
        self.plugin_manager = plugin_manager
        self.metadata_gen = PluginMetadataGenerator()
    

    def get_package_metadata(self, package_id: str) -> Metadata:
        metadata_folder = self.get_plugin_metadata_folder(package_id)
        if not metadata_folder.exists():
            metadata = self.metadata_gen.generate_from_manifest(
                self.plugin_manager.ensure_package(package_id)
            )
            self.save_package_metadata(metadata)
            return metadata

        metadata = MetadataFileUtils.load_from_folder(metadata_folder)
        return metadata

    def get_package_metadata_manifest(self, package_id: str) -> MetadataManifest:
        metadata_folder = self.get_plugin_metadata_folder(package_id)
        if metadata_folder.exists():
            return _MetadataLoad._load_header(metadata_folder)

        metadata = self.get_package_metadata(package_id)
        return MetadataManifest(
            **metadata.__dict__
        )

    def save_package_metadata(self, metadata: Metadata):
        # if not self.plugin_manager.is_package_loaded(metadata.package_id):
        #     raise Exception("Can't save metadata of a package that is not loaded.")
        metadata_folder = self.get_plugin_metadata_folder(metadata.package_id)
        metadata_folder.mkdir(exist_ok=True)

        MetadataFileUtils.save_to_folder(metadata, metadata_folder)

    # Utils

    def get_plugin_metadata_folder(self, package_id: str) -> Path:
        return self.plugins_folder / package_id / METADATA_FOLDER_NAME

