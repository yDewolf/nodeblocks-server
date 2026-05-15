from typing import Annotated, Optional

from pydantic import BaseModel

from nodeserver.api.base_server import NodeServer
from nodeserver.api.node.node_parameters import FileParam, Param
from nodeserver.api.node.nodes import BaseNode
from nodeserver.api.node.slots import Input, InputSlotIO, NodeSlot, Output
from nodeserver.wrapper.nodes.data.node_data_types import FILE_TYPE

import logging
import logging.config

from nodeserver.wrapper.nodes.data.node_metadata import INPUT_CATEGORY, NodeCategory, NodeMetadata, NodeTag
from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror, SlotMirror
from nodeserver.wrapper.utils.type_reader_utils import TypeReaderUtils

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("root")

MATH_CATEGORY = NodeCategory(
    super_category=None, 
    name="Math", 
    description=""
)

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

    _metadata: NodeMetadata = NodeMetadata(
        category=INPUT_CATEGORY,
        capitalized_type="InputNode",
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
    _metadata: NodeMetadata = NodeMetadata(
        category=INPUT_CATEGORY,
        capitalized_type="FileInputNode",
        tags=[NodeTag(tag_name="output/file")]
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
    
    _metadata: NodeMetadata = NodeMetadata(
        category=MATH_CATEGORY,
        capitalized_type=""
    )

class SumNode(MyMathNode): operation = 0
class SubNode(MyMathNode): operation = 1
class MulNode(MyMathNode): operation = 2
class DivNode(MyMathNode): operation = 3

class TestNode(BaseNode):
    class Slots:
        slot_0: NodeSlot[InputSlotIO[list[float]]]

NODE_REGISTRY: dict[str, type[BaseNode]] = {
    "MyInputNode": MyInputNode,
    "FileInputNode": FileInputNode,
    "SumNode": SumNode,
    "SubNode": SubNode,
    "MulNode": MulNode,
    "DivNode": DivNode,
    "TestNode": TestNode
}

my_cool_types = TypeReaderUtils.make_types_from_registry(0, "MyCoolTypes", NODE_REGISTRY)
server = NodeServer(my_cool_types)
server.run_server()