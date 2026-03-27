import logging

from nodeserver.api.base_nodes import BaseNode
from nodeserver.networking.nodes.data.node_data_types import BaseNodeType
from nodeserver.networking.nodes.helpers.file.typing_file_reader import TypeFileReader
from test_data import TYPE_FILE_JSON

LOGGER = logging.Logger("Logger")

types_file = TypeFileReader()
types_file._load_json_data(
    TYPE_FILE_JSON
)

nodes = []
for idx, type_name in enumerate(types_file.node_constructors):
    constructor = types_file.get_constructor(type_name)
    if not constructor:
        continue
    
    mirror = constructor.make_node_mirror(
        type_name, idx,
    )
    if not mirror:
        LOGGER.error(f"ERROR: Couldn't make mirror using constructor {idx}: {constructor}")
        continue

    node = BaseNode(mirror)
    nodes.append(node)

pass