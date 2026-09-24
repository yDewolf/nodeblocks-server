from typing import Any, Callable, Optional

from pydantic import BaseModel, PrivateAttr


# Any BaseNode's Parameters class should inherit this
class NodeParameters(BaseModel):
    _on_change: Optional[Callable[[str, Any], None]] = PrivateAttr(default=None)

    def bind_sync(self, callback: Callable[[str, Any], None]) -> None:
        self._on_change = callback

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        
        if not name.startswith("_") and self._on_change:
            self._on_change(name, getattr(self, name))
