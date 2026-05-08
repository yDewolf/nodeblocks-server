from typing import Annotated, Optional

from pydantic import BaseModel

from nodeserver.api.base_server import NodeServer
from nodeserver.api.node.node_exceptions import NoOutputException
from nodeserver.api.node.node_parameters import FileParam, Param
from nodeserver.api.node.node_utils import NodeUtils
from nodeserver.api.node.nodes import BaseNode
from nodeserver.api.node.slots import Input, Output
from nodeserver.wrapper.nodes.data.node_data import NodeData
from nodeserver.wrapper.nodes.data.node_data_types import FILE_TYPE, INPUT_TYPE, OUTPUT_TYPE, BaseSlotType, DataTypes, SuperSlotTypes
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
    class Parameters(BaseModel):
        value: Annotated[float, Param(
            label="Value",
        )] = 0.0
    _parameters: Parameters

    def forward(self, input: BaseModel) -> _InputNodeOutput:
        value = self._parameters.value
        if value == None:
            # raise NoOutputException()
            return _InputNodeOutput(out_0=None)
        
        if type(value) != float and type(value) != int:
            return _InputNodeOutput(out_0=None)
        
        return _InputNodeOutput(
            out_0=value
        )

class _FileInput_Out(BaseModel):
    out_0: Annotated[Optional[str], Output(datatype_override=FILE_TYPE)]
class FileInputNode(MyInputNode):
    OutputModel = _FileInput_Out
    class Parameters(BaseModel):
        file_path: Annotated[str, FileParam(
            label="Path",
            extension_filter=[".json"],
        )] = ""
    _parameters: Parameters


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
class SumNode(MyMathNode): operation = 0
class SubNode(MyMathNode): operation = 1
class MulNode(MyMathNode): operation = 2
class DivNode(MyMathNode): operation = 3

NODE_REGISTRY: dict[str, type[BaseNode]] = {
    "MyInputNode": MyInputNode,
    "FileInputNode": FileInputNode,
    "SumNode": SumNode,
    "SubNode": SubNode,
    "MulNode": MulNode,
    "DivNode": DivNode,
}
node_constructors: list[ConstructorModel] = []
slot_types = {}
for node_type in NODE_REGISTRY:
    super_slot_types, constructor = NODE_REGISTRY[node_type].generate_types(slot_types)
    node_constructors.append(constructor)
    slot_types = super_slot_types

def auto_parser(mirror: NodeMirror) -> BaseNode:
    node_class = NODE_REGISTRY.get(mirror.type_name, None)
    if not node_class:
        raise Exception(f"Couldn't parse node with type {mirror.type_name}")

    return node_class(mirror)

my_cool_types = TypeFileReader.new(0, "MyCoolTypes", slot_types, [])
my_cool_types.set_new_constructors(TypeReaderUtils.make_constructors(
    my_cool_types, {}, auto_parser, node_constructors
))

server = NodeServer(my_cool_types)
server.run_server()