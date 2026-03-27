import json


TYPE_FILE_JSON = json.loads(
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
        "SumNode": {
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

SCENE_DATA_JSON = json.loads(
"""
{
    "node_types_id": "some_nodepack",
    "node_types_version": 0,
    "nodes": {
        "node_0": {
            "type": "SumNode",
            "position": [500, 0],
            "size": [100, 50],
            "data": {}
        },
        "node_1": {
            "type": "NodeType",
            "position": [700, 300],
            "size": [100, 50],
            "data": {}
        },
        "node_2": {
            "type": "NodeType",
            "position": [900, 100],
            "size": [100, 50],
            "data": {}
        }
    },
    "connections": {
        "c1": {
            "from": "nodes:node_0:slots:out_0",
            "to": "nodes:node_1:slots:in_0"
        },
        "c2": {
            "from": "nodes:node_0:slots:out_0",
            "to": "nodes:node_2:slots:in_0"
        }
    }
} 
"""
)