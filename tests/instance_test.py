import json
from logging import Logger

from nodeserver.api.base_nodes import BaseNode
from nodeserver.api.instance_states import InstanceCommands, InstanceStates, LoopStates
from nodeserver.api.internal.instance_manager import InstanceManager
from nodeserver.api.server_instance import ServerInstance
from nodeserver.networking.nodes.data.node_data import NodeData
from nodeserver.networking.nodes.data.node_data_types import FLOAT_TYPE, INPUT_TYPE, OUTPUT_TYPE, BaseSlotType, SuperSlotTypes
from nodeserver.networking.nodes.helpers.file.type_dataclasses import NodeParameterData, SlotData
from nodeserver.networking.nodes.helpers.file.typing_file_reader import TypeFileReader
from nodeserver.networking.nodes.helpers.node_constructor import CustomMirrorConstructor
from nodeserver.networking.nodes.node.base_nodes import NodeMirror, SlotMirror

LOGGER = Logger("logger")
manager = InstanceManager()

class MyInputNode(BaseNode):
    def forward(self, input: dict[SlotMirror, dict[SlotMirror, dict]]):
        parameter = self._mirror.data.parameters.get("value")
        if parameter == None:
            return {}
        
        if type(parameter.value) != float and type(parameter.value) != int:
            return {}
        
        output_data = {
            "out_0": parameter.value
        }
        return self.map_to_slots(output_data)


class MyMathNode(BaseNode):
    operation: int = -1
    def __init__(self, mirror: NodeMirror | None = None):
        super().__init__(mirror)

    def forward(self, input: dict[SlotMirror, dict[SlotMirror, dict]]):
        input_values: list[float] = []
        for slot_type, slots in self._mirror.slots.items():
            if slot_type != SuperSlotTypes.INPUT: continue

            for slot in slots:
                slot_outputs = input.get(slot)
                if not slot_outputs: continue
                
                for out_slot, output in slot_outputs.items():
                    output_value = output.get("value")
                    if not output_value: continue

                    input_values.append(output_value)
        
        if len(input_values) < 2:
            return input_values
        
        result = 0
        match self.operation:
            case 0: result = sum(input_values)
            case 1: result = input_values[0] - input_values[1]
            case 2: result = input_values[0] * input_values[1]
            case 3: result = input_values[0] / input_values[1]
        
        print(f"Operation {self.operation} resulted in {result} with inputs {input_values}")
        return self.map_to_slots({
            "out_0": result
        })


test_scene = json.loads(
"""
{
    "node_types_id": "MyCoolTypes",
    "node_types_version": 0,
    "nodes": {
        "node_2": {
            "type": "SumNode",
            "data": {}
        },
        "node_3": {
            "type": "MulNode",
            "data": {}
        },
        "node_0": {
            "type": "InputNode",
            "data": {"value": 39}
        },
        "node_1": {
            "type": "InputNode",
            "data": {"value": 28}
        },
        "node_4": {
            "type": "InputNode",
            "data": {"value": 0.1}
        }
    },
    "connections": {
        "c1": {
            "from": "nodes:node_0:slots:out_0",
            "to": "nodes:node_2:slots:in_0"
        },
        "c4": {
            "from": "nodes:node_4:slots:out_0",
            "to": "nodes:node_3:slots:in_0"
        },
        "c2": {
            "from": "nodes:node_1:slots:out_0",
            "to": "nodes:node_2:slots:in_1"
        },
        "c3": {
            "from": "nodes:node_2:slots:out_0",
            "to": "nodes:node_3:slots:in_0"
        }
    }
} 
"""
)

slot_types: dict[str, BaseSlotType] = {
    "input": INPUT_TYPE,
    "output": OUTPUT_TYPE
}
default_slots: dict[str, SlotData] = {
    "in_0": SlotData("input", None),
    "in_1": SlotData("input", None),
    "out_0": SlotData("output", None),
}

def my_parser(mirror: NodeMirror) -> BaseNode:
    if mirror.type_name == "InputNode":
        return MyInputNode(mirror)
    
    node = MyMathNode(mirror)
    match mirror.type_name:
        case "SumNode": node.operation = 0
        case "SubNode": node.operation = 1
        case "MulNode": node.operation = 2
        case "DivNode": node.operation = 3 

    return node

my_cool_types = TypeFileReader.new(0, "MyCoolTypes", [
    CustomMirrorConstructor(
        "InputNode", NodeData({"value": NodeParameterData("float", None)}),
        slot_types,
        {"out_0": SlotData("output", None)},
        my_parser
    ),
    CustomMirrorConstructor(
        "SumNode", NodeData({}),
        slot_types,
        default_slots,       
        my_parser
    ),
    CustomMirrorConstructor(
        "SubNode", NodeData({}),
        slot_types,
        default_slots,
        my_parser
    ),
    CustomMirrorConstructor(
        "MulNode", NodeData({}),
        slot_types,
        default_slots,       
        my_parser,
    ),
    CustomMirrorConstructor(
        "DivNode", NodeData({}),
        slot_types,
        default_slots,
        my_parser
    )
])

my_instance = ServerInstance(my_cool_types)
result = manager.set_instance(
    "someRandomString", my_instance
)
print(f"Created instance? {result}")
my_instance.start_running()
# my_instance.load_types(TYPE_FILE_JSON)
my_instance.load_new_scene(test_scene)

# my_instance.mirror_manager.connection_manager.remove_connection(
#     "c4"
# )
# my_instance.mirror_manager.connection_manager.remove_connection(
#     "c3"
# )

while True:
    command = input("\nWaiting for command: \n>> ")
    match command.upper():
        case "SET_STATE":
            new_state = int(input("New State: \n>> "))
            my_instance.state_controller.queue_state(
                InstanceStates(new_state)
            )

        case "SET_LOOP_STATE":
            new_state = int(input("New State: \n>> "))
            my_instance.state_controller.queue_loop_state(
                LoopStates(new_state)
            )

        case "STEP":
            my_instance.state_controller.queue_command(
                InstanceCommands.STEP_NEXT
            )

        case "RESUME":
            my_instance.state_controller.queue_command(
                InstanceCommands.RESUME_LOOP
            )

        case "STOP":
            my_instance.state_controller.queue_command(
                InstanceCommands.STOP
            )