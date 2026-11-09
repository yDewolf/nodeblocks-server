
from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version, parse as parse_version


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

    @staticmethod
    def public_version(version: str) -> str:
        """'2.13.0+cu126' -> '2.13.0'"""
        try:
            return Version(version).public

        except InvalidVersion:
            return version.split("+", 1)[0]

    @staticmethod
    def to_requirement(name: str, spec: str) -> str:
        """
        {"torch": ">=2.11.0"} -> "torch>=2.11.0".
        Accepts spec="*" (any version) and "1.2.3" as a shortcut for "==1.2.3".
        Name might contain extras.
        """
        spec = (spec or "").strip()
        if spec in ("", "*"):
            text = name

        elif spec[0].isdigit():
            text = f"{name}=={spec}"

        else:
            text = f"{name}{spec}"

        try:
            Requirement(text)

        except InvalidRequirement as e:
            raise ValueError(f"Invalid python dependency {name!r}: {spec!r} ({e})") from e

        return text

    @staticmethod
    def constraints_text(freeze: dict[str, str]) -> str:
        return "\n".join(
            f"{name}=={VersionHelper.public_version(version)}" for name, version in sorted(freeze.items())
        )

    @staticmethod
    def unsatisfied_by_env(requirements: list[str], freeze: dict[str, str]) -> list[str]:
        unsatisfied: list[str] = []
        for text in requirements:
            req = Requirement(text)
            if req.marker is not None and not req.marker.evaluate({"extra": ""}):
                continue

            installed = freeze.get(canonicalize_name(req.name))
            if installed and not req.extras and req.specifier.contains(installed, prereleases=True):
                continue

            unsatisfied.append(text)

        return unsatisfied
