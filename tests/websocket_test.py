from typing import Annotated, Optional

from pydantic import BaseModel

from nodeserver.api.base_server import NodeServer
from nodeserver.api.node.node_exceptions import NoOutputException
from nodeserver.api.node.nodes import BaseNode
from nodeserver.api.node.slots import Input
from nodeserver.wrapper.nodes.data.node_data import NodeData
from nodeserver.wrapper.nodes.data.node_data_types import INPUT_TYPE, OUTPUT_TYPE, BaseSlotType, DataTypes, SuperSlotTypes
from nodeserver.wrapper.nodes.helpers.file.type_dataclasses import NodeFileParameter, NodeNumberParameter, SlotData
from nodeserver.wrapper.nodes.helpers.file.typing_file_reader import ConstructorModel, TypeFileReader, TypeReaderUtils

import logging
import logging.config

from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror, SlotMirror

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("root")

class _InputNodeOutput(BaseModel):
    out_0: Optional[float]

class MyInputNode(BaseNode):
    OutputModel = _InputNodeOutput

    def forward(self, input: BaseModel) -> _InputNodeOutput:
        parameter = self._mirror.data.parameters.get("value")
        if parameter == None:
            # raise NoOutputException()
            return _InputNodeOutput(out_0=None)
        
        if type(parameter.value) != float and type(parameter.value) != int:
            return _InputNodeOutput(out_0=None)
        
        return _InputNodeOutput(
            out_0=parameter.value
        )


class _MathNodeInput(BaseModel):
    in_0: float
    in_1: Annotated[list[float], Input(max_inputs=3)]
class _MathNodeOutput(BaseModel):
    out_0: float

class MyMathNode(BaseNode):
    InputModel = _MathNodeInput
    OutputModel = _MathNodeOutput

    operation: int = -1
    def __init__(self, mirror: NodeMirror | None = None):
        super().__init__(mirror)

    def forward(self, input: _MathNodeInput) -> _MathNodeOutput:
        result = 0
        match self.operation:
            case 0: result = input.in_0 + sum(input.in_1)
            case 1: result = input.in_0 - sum(input.in_1)
            case 2: result = input.in_0 * sum(input.in_1)
            case 3: result = input.in_0 / sum(input.in_1)
        
        logger.info(f"Operation {self.operation} resulted in {result} with inputs {input}")
        return _MathNodeOutput(
            out_0=result
        )


slot_types: dict[str, BaseSlotType] = {
    "input": INPUT_TYPE,
    "output": OUTPUT_TYPE
}
default_slots: dict[str, SlotData] = {
    "in_0": SlotData(type="input", data_type=DataTypes.FLOAT),
    "in_1": SlotData(type="input", data_type=DataTypes.FLOAT),
    "out_0": SlotData(type="output", data_type=DataTypes.FLOAT),
}

def my_parser(mirror: NodeMirror) -> BaseNode:
    if mirror.type_name == "InputNode" or mirror.type_name == "FileInputNode":
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
        ConstructorModel.new("FileInputNode", NodeData({"file": NodeFileParameter(extension_filter=["json"])}), {"out_0": SlotData(type="output", data_type=DataTypes.FILE)}),
        ConstructorModel.new("InputNode", NodeData({"value": NodeNumberParameter(type=DataTypes.FLOAT)}), {"out_0": SlotData(type="output", data_type=DataTypes.FLOAT)}),
        ConstructorModel.new("SumNode"),
        ConstructorModel.new("SubNode"),
        ConstructorModel.new("MulNode"),
        ConstructorModel.new("DivNode"),
    ]
))

server = NodeServer(my_cool_types)
server.run_server()