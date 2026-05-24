from typing import Optional, Type

from nodeserver.wrapper.nodes.data.node_data_types import DefaultDataTypes

class ParamConfig:
    label: Optional[str]
    min: Optional[float]
    max: Optional[float]
    step: Optional[float]
    options: Optional[list]

    def __init__(
        self, 
        # TODO: Implement these (here and on client) -> 
        # widget: str = "number",
        label: Optional[str] = None, 
        min: Optional[float] = None,
        max: Optional[float] = None,
        step: Optional[float] = None,
        options: Optional[list] = None,
        option_type: Optional[DefaultDataTypes] = None,
        **kwargs
    ):
        # self.widget = widget
        self.label = label
        self.min = min
        self.max = max
        self.step = step
        self.options = options
        self.option_type = option_type
        self._extra = kwargs
    
    def dump(self) -> dict:
        return {
            "label": self.label, 
            "min": self.min,
            "max": self.max,
            "step": self.step,
            "options": self.options,
            "option_type": self.option_type,
            **self._extra
        }

def Param(label: Optional[str] = None, **kwargs):
    return ParamConfig(label=label, **kwargs)

def BooleanParam(label: Optional[str] = None):
    return ParamConfig(label=label, type=DefaultDataTypes.BOOLEAN)

def FileParam(label: Optional[str] = None, extension_filter: Optional[list[str]] = None, **kwargs):
    return ParamConfig(label=label, type=DefaultDataTypes.FILE, extension_filter=extension_filter, **kwargs)

def OptionParam(options: list, option_type: DefaultDataTypes, label: Optional[str] = None, **kwargs):
    return ParamConfig(type=DefaultDataTypes.OPTIONS, options=options, option_type=option_type, label=label, **kwargs)
