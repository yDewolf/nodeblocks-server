import json
import logging

from nodeserver.api.base_nodes import BaseNode
from nodeserver.networking.nodes.data.node_data_types import BaseNodeType
from nodeserver.networking.nodes.helpers.typing_file_reader import TypingFile

LOGGER = logging.Logger("Logger")

types_file = TypingFile()
types_file._load_json_data(
    json.loads(
        """
        {
            "version": 0,
            "id": "some_nodepack",
            "slot_types": {
                "input": {
                    "extends": "input_slot",
                    "default_data_type": "float",
                    "conn_whitelist": ["#output_slot"]
                },
                "output": {
                    "extends": "output_slot",
                    "default_data_type": "float",
                    "conn_whitelist": ["#input_slot"]
                },
                "some_other_type": {
                    "extends": "custom_type",
                    "default_data_type": "float",
                    "conn_whitelist": ["#output_slot"]
                }
            },
            "node_types": {
                "NodeType": {
                    "description": "Takes a float input and outputs it without any modifications",
                    "parameters": {"out_features": {"type": "uint", "range": [1, -1]}, "some_parameter": {"type": "float", "range": [1, 10]}},
                    "slots": {
                        "in_0": {"type": "input", "tooltip": "Main input value"},
                        "in_1": {"type": "input", "data_type": "uint", "tooltip": "Test"},
                        "out_0": {"type": "output", "tooltip": "Takes the value from ${in_0}, and outputs it"}
                    }
                },
                "OtherNodeType": {
                    "description": "Takes a float input and outputs it without any modifications",
                    "parameters": {"out_features": {"type": "uint"}, "some_parameter": {"type": "float", "range": [1, 10]}},
                    "slots": {
                        "in_1": {"type": "input", "data_type": "uint", "tooltip": "Test"},
                        "out_0": {"type": "output", "data_type": "uint", "tooltip": "Takes the value from ${in_0}, and outputs it"}
                    }
                }
            }
        }
        """
    )
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

    node = BaseNode.from_mirror(mirror)
    nodes.append(node)

pass