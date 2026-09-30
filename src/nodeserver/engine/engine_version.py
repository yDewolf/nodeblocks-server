from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import tomllib

PACKAGE_NAME = "nodeserver"
def _resolve_engine_version() -> str:
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
                if pyproject_version: return pyproject_version

    except Exception:
        pass

    return "0.0.0-dev"

try:
    CURRENT_ENGINE_VERSION = version("nodeserver")

except PackageNotFoundError:
    CURRENT_ENGINE_VERSION = "0.0.0-dev"


CURRENT_ENGINE_VERSION = _resolve_engine_version()