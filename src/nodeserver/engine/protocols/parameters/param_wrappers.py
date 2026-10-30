from typing import Any, Optional, Union

from pydantic import Field

from nodeserver.engine.protocols.parameters.node_parameter import ParamArguments
from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec

# TODO: melhorar a forma como passamos esses argumentos aqui
# para gerar o ParamArguments
def ParamField(
    default: Any = ..., 
    required: bool = False,
    label: Optional[str] = None, # TODO: let client use metadata instead
    min: Optional[float] = None, 
    max: Optional[float] = None, 
    step: Optional[float] = None, 
    options: Optional[list] = None,
    extension_filter: Optional[list[str]] = None,
    datatype: Optional[Union[DataTypeSpec, str]] = None, # spec obj or fully qualified path
    **kwargs
) -> Any:
    datatype_fqn: str = "core:unknown"
    if datatype is not None: 
        if isinstance(datatype, DataTypeSpec):
            datatype_fqn = datatype.fqn
        else:
            datatype_fqn = datatype

    param_meta: ParamArguments = ParamArguments(datatype_fqn=datatype_fqn, required=required)
    if step is not None: param_meta.step = step
    if options is not None: param_meta.options = options
    if min is not None: param_meta.min = min
    if max is not None: param_meta.max = max
    if extension_filter is not None: param_meta.extension_filter = extension_filter
    
    return Field(
        default=default,
        title=label,
        ge=min, # greater or equal
        le=max, # less or equal
        json_schema_extra=param_meta.model_dump(),
        **kwargs
    )

def Param(label: Optional[str] = None, required: bool = False, datatype: Optional[Union[DataTypeSpec, str]] = None, **kwargs):
    return ParamField(label=label, required=required, datatype=datatype, **kwargs)

def BooleanParam(label: Optional[str] = None, required: bool = False, **kwargs):
    return ParamField(label=label, required=required, datatype_id="core.bool", **kwargs)
