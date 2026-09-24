from typing import Any, Optional, Union

from pydantic import Field

from nodeserver.protocols.manifest.node.datatypes import DataTypeSpec


def ParamField(
    default: Any = ..., 
    label: Optional[str] = None, # TODO: let client use metadata instead
    min: Optional[float] = None, 
    max: Optional[float] = None, 
    step: Optional[float] = None, 
    options: Optional[list] = None,
    datatype: Optional[Union[DataTypeSpec, str]] = None, # spec obj or fully qualified path
    **kwargs
) -> Any:
    ui_meta = {}
    if step is not None: ui_meta["step"] = step
    if options is not None: ui_meta["options"] = options
    if datatype is not None: 
        datatype_fqn: str
        if isinstance(datatype, DataTypeSpec):
            datatype_fqn = datatype.fqn
        
        ui_meta["datatype"] = datatype_fqn
    
    return Field(
        default=default,
        title=label,
        ge=min, # greater or equal
        le=max, # less or equal
        json_schema_extra=ui_meta,
        **kwargs
    )

def Param(label: Optional[str] = None, datatype_id: Optional[str] = None, **kwargs):
    return ParamField(label=label, **kwargs)

def BooleanParam(label: Optional[str] = None, **kwargs):
    return ParamField(label=label, datatype_id="core.bool", **kwargs)
