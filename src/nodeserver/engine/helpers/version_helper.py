
from packaging.specifiers import SpecifierSet
from packaging.version import parse as parse_version


class VersionHelper:
    @staticmethod
    def _parse_semver_specifier(version_req: str) -> SpecifierSet:
        """
        Converts a version string to a packaging SpecifierSet
        if no operators are found, applies SemVer compatibility rules
        - "1.2.0"  -> ">=1.2.0, <2.0.0"
        - "0.2.1"  -> ">=0.2.1, <0.3.0"
        """

        if any(op in version_req for op in "<>=!~"):
            return SpecifierSet(version_req)

        v = parse_version(version_req)
        if v.major == 0:
            upper_bound = f"0.{v.minor + 1}.0"
        else:
            upper_bound = f"{v.major + 1}.0.0"

        return SpecifierSet(f">={version_req}, <{upper_bound}")
