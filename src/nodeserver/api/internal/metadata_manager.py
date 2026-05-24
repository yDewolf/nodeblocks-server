
from pathlib import Path
import time
from typing import Callable, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from nodeserver.wrapper.metadata.helpers.metadata_utils import METADATA_EXTENSION, METADATA_FOLDER_NAME, ROOT_METADATA_PATH, MetadataFileUtils
from nodeserver.wrapper.metadata.metadata_file import MetadataFile
from nodeserver.wrapper.metadata.metadata_header import Metadata, MetadataVersion
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import TypeFileReader

class MetadataFolderWatchdog(FileSystemEventHandler):
    def __init__(self, callback_on_change: Callable[[Path], None]):
        super().__init__()
        self.callback_on_change = callback_on_change

    def on_modified(self, event):
        if event.is_directory:
            return
            
        if event.src_path.endswith(METADATA_EXTENSION): # type: ignore
            self.callback_on_change(Path(str(event.src_path)))


class MetadataManager:
    indexed_metadata: dict[str, MetadataFile]
    _handle_metadata_update: Callable[[str], None]
    last_reload_time: float = 0.0

    def __init__(self, handle_metadata_update: Callable[[str], None]) -> None:
        self.indexed_metadata = {}
        self._handle_metadata_update = handle_metadata_update

        self.observer = Observer()
        self.handler = MetadataFolderWatchdog(self.handle_disk_update)

    def index_metadata_for_type(self, type_reader: TypeFileReader):
        if not type_reader._node_types_id: 
            raise Exception("TypeReader doesn't have _node_types_id set")

        if self.indexed_metadata.__contains__(type_reader._node_types_id):
            return

        metadata = MetadataFile.new(type_reader, True)
        self.indexed_metadata[type_reader._node_types_id] = metadata

    # Watchdog stuff
    def start_watching(self):
        self.observer.schedule(self.handler, ROOT_METADATA_PATH, recursive=True)
        self.observer.start()
        print(f"Watchdog is observing {ROOT_METADATA_PATH}")

    def stop_watching(self):
        self.observer.stop()
        self.observer.join()

    def handle_disk_update(self, file_path: Path):
        now = time.time()
        if now - self.last_reload_time < 0.5:
            return
        
        previous_part: str = ""
        type_id: Optional[str] = None
        for idx in range(1, len(file_path.parts)):
            current_part = file_path.parts[-idx]
            if current_part == METADATA_FOLDER_NAME:
                type_id = previous_part
                break

            previous_part = current_part

        if not type_id: return

        metadata_file = self.indexed_metadata.get(type_id)
        if not metadata_file: return
        
        metadata_file.reload_from_disk(only_if_modified=False)
        self.last_reload_time = now
        self._handle_metadata_update(type_id)
        # print(f"Detected change on {file_path}. type_id: {type_id}")

    # Manual syncing
    def get_unsynced_metadata(self) -> list[str]:
        """
            Returns a list with the id of Types that have changes on their metadata.
        """
        updated_metadata: list[str] = []
        for type_id, metadata_file in self.indexed_metadata.items():
            if metadata_file.has_modifications_on_disk():
                updated_metadata.append(type_id)
                metadata_file.reload_from_disk(only_if_modified=False)
        
        return updated_metadata

    def get_metadata_version(self, type_id: str) -> MetadataVersion:
        metadata_file = self.indexed_metadata.get(type_id, None)
        if not metadata_file:
            raise Exception(f"Couldn't find metadata related to type id: {type_id}")
        
        if not metadata_file.metadata:
            raise Exception(f"Metadata file (type_id: {type_id}) doesn't have a metadata loaded")

        return MetadataVersion(
            types_version=metadata_file.metadata.types_version,
            meta_version=metadata_file.metadata.meta_version
        )

    def get_metadata(self, type_id: str) -> Optional[Metadata]:
        metadata_file = self.indexed_metadata.get(type_id)
        if not metadata_file:
            return None

        return metadata_file.metadata 