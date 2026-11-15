"""
Engine Version Specifications:
- Major -> changes on how graphs are processed that might break existent nodes;
- Minor -> new features that don't break existent stuff;
- Micro -> fixes.
"""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import tomllib

from packaging.version import InvalidVersion, Version

PACKAGE_NAME = "nodeblocks"

def get_raw_package_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        pass

    try:
        current_dir = Path(__file__).resolve().parent
        for parent in [current_dir] + list(current_dir.parents):
            pyproject_path = parent / "pyproject.toml"
            if not pyproject_path.exists():
                continue

            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                pyproject_version = data.get("project", {}).get("version")
                
                if pyproject_version:
                    return pyproject_version
    
    except Exception:
        pass

    return "0.0.0-dev"

def _resolve_engine_version() -> str:
    raw = get_raw_package_version()
    try:
        return Version(raw).base_version
    except InvalidVersion:
        return raw.split("+")[0]

CURRENT_ENGINE_VERSION = _resolve_engine_version()
pass