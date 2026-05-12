from typing import Optional

from nodeserver.wrapper.nodes.data.node_data_types import DataTypes

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
        **kwargs
    ):
        # self.widget = widget
        self.label = label
        self.min = min
        self.max = max
        self.step = step
        self.options = options
        self._extra = kwargs
    
    def dump(self) -> dict:
        return {
            "label": self.label, 
            "min": self.min,
            "max": self.max,
            "step": self.step,
            "options": self.options,
            **self._extra
        }

def Param(label: Optional[str] = None, **kwargs):
    return ParamConfig(label=label, **kwargs)

def FileParam(label: Optional[str] = None, extension_filter: Optional[list[str]] = None, **kwargs):
    return ParamConfig(label=label, type=DataTypes.FILE, extension_filter=extension_filter, **kwargs)
