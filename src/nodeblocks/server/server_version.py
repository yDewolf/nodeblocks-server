from packaging.specifiers import SpecifierSet

SERVER_API_VERSION: str = "0.2.0"
SERVER_API_COMPAT_SPECIFIER: SpecifierSet = SpecifierSet(f">={SERVER_API_VERSION}")
