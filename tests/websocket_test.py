import os
from typing import Annotated, Optional

from pydantic import BaseModel

from nodeserver.api.base_server import NodeServer
from nodeserver.api.instance.instance_runtime import ContextAwareInput
from nodeserver.api.node.node_parameters import BooleanParam, FileParam, OptionParam, Param
from nodeserver.api.node.nodes import BaseNode, NoInput
from nodeserver.api.node.slots import Input, NodeSlot, Output

import logging
import logging.config

from nodeserver.api.utils.file_utils import get_project_root
from nodeserver.api.web.instance.special_instance import WorkspaceAwareInput
from nodeserver.wrapper.metadata.metadata_file import MetadataFile
from nodeserver.wrapper.metadata.nodes.node_metadata import INPUT_CATEGORY, NodeCategory, NodeTag, NodeTypeMeta
from nodeserver.wrapper.nodes.data.node_data_types import DefaultDataTypes, DefaultRenderers
from nodeserver.wrapper.nodes.node.base_nodes import NodeMirror, SlotMirror
from nodeserver.wrapper.utils.type_reader_utils import TypeReaderUtils

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("root")

MATH_CATEGORY = NodeCategory(
    super_category=None, 
    category_id="Math", 
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

    _metadata: NodeTypeMeta = NodeTypeMeta(
        category=INPUT_CATEGORY,
        capitalized_name="InputNode",
    )

class _FileInput_Out(BaseModel):
    out_0: Annotated[Optional[str], Output(
        base_type_override=DefaultDataTypes.FILE, 
        renderer_override=DefaultRenderers.TEXT
    )] # TODO: Implement FileOutput SlotIO

class FileInputNode(BaseNode):
    InputModel = WorkspaceAwareInput
    OutputModel = _FileInput_Out
    class Parameters(BaseModel):
        file_path: Annotated[str, FileParam(
            label="Path",
            extension_filter=[".json"],
        )] = ""
        test_parameter: Annotated[str, OptionParam(
            options=["option 1", "option 2", "option 3"],
            option_type=DefaultDataTypes.TEXT
        )] = "option 3"
        test_boolean: Annotated[bool, BooleanParam()] = True

    _parameters: Parameters
    _metadata: NodeTypeMeta = NodeTypeMeta(
        category=INPUT_CATEGORY,
        capitalized_name="FileInputNode",
        tags=[NodeTag(tag_id="output/file")]
    )

    def forward(self, input: WorkspaceAwareInput) -> _FileInput_Out:
        if not self._parameters.file_path:
            raise Exception("No file was selected")

        uploads_path = input._workspace.get_uploads_path()
        target_file_path = os.path.join(uploads_path, self._parameters.file_path)
        logger.info(f"Will read data from file {target_file_path}")
        logger.info(f"Assigned test_parameter to {self._parameters.test_parameter}")
        logger.info(f"Assigned test_boolean to {self._parameters.test_boolean}")
        file_content = ""
        with open(target_file_path, "r") as file:
            file_content = file.read()

        return _FileInput_Out(
            out_0=file_content
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
    
    _metadata: NodeTypeMeta = NodeTypeMeta(
        category=MATH_CATEGORY,
        capitalized_name=""
    )

class SumNode(MyMathNode): operation = 0
class SubNode(MyMathNode): operation = 1
class MulNode(MyMathNode): operation = 2
class DivNode(MyMathNode): operation = 3

class TestNode(BaseNode):
    class Slots:
        slot_0: Annotated[list[float], Input()]

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
metadata_file = MetadataFile.new(my_cool_types)
metadata_file.save_on_metadata()

loaded_meta = MetadataFile()
loaded_meta.load_from_metadata(my_cool_types._node_types_id or "")

server = NodeServer(my_cool_types)
server.run_server()