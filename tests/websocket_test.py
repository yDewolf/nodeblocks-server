
import asyncio

from nodeserver.api.instance.base_nodes import BaseNode
from nodeserver.api.websocket_manager import WebsocketInstanceManager
from nodeserver.wrapper.nodes.data.node_data import NodeData
from nodeserver.wrapper.nodes.data.node_data_types import INPUT_TYPE, OUTPUT_TYPE, BaseSlotType, SuperSlotTypes
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import NodeParameterData, SlotData
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import ConstructorModel, TypeFileReader, TypeReaderUtils
from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror, SlotMirror

import logging
import logging.config

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("root")

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
        
        logger.info(f"Operation {self.operation} resulted in {result} with inputs {input_values}")
        return self.map_to_slots({
            "out_0": result
        })


slot_types: dict[str, BaseSlotType] = {
    "input": INPUT_TYPE,
    "output": OUTPUT_TYPE
}
default_slots: dict[str, SlotData] = {
    "in_0": SlotData(type="input", data_type="float"),
    "in_1": SlotData(type="input", data_type="float"),
    "out_0": SlotData(type="output", data_type="float"),
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


my_cool_types = TypeFileReader.new(0, "MyCoolTypes", slot_types, [])
my_cool_types.set_new_constructors(TypeReaderUtils.make_constructors(
    my_cool_types, default_slots, my_parser, [
        ConstructorModel.new("InputNode", NodeData({"value": NodeParameterData(type="float")}), {"out_0": SlotData(type="output", data_type="float")}),
        ConstructorModel.new("SumNode"),
        ConstructorModel.new("SubNode"),
        ConstructorModel.new("MulNode"),
        ConstructorModel.new("DivNode"),
    ]
))

manager = WebsocketInstanceManager(my_cool_types)
asyncio.run(manager.run_server())