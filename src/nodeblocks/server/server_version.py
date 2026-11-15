from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version

from nodeblocks.engine.engine_version import get_raw_package_version

def _resolve_server_api_version() -> str:
    raw = get_raw_package_version()
    try:
        parsed = Version(raw)
        if parsed.local and parsed.local.startswith("server."):
            return parsed.local.removeprefix("server.")
    
    except InvalidVersion:
        pass

    return "0.0.0"

SERVER_API_VERSION: str = _resolve_server_api_version()
SERVER_API_COMPAT_SPECIFIER: SpecifierSet = SpecifierSet(f">={SERVER_API_VERSION}")
