import logging
import shutil
import hashlib, os, subprocess, sys, tempfile
from importlib.metadata import distributions
from pathlib import Path
from typing import Optional, Union

from filelock import FileLock
from packaging.utils import canonicalize_name

from nodeserver.engine.exceptions.plugin.plugin_internal_exceptions import PluginPythonDependencyError
from nodeserver.engine.plugins.protocols.plugin_manifest import EnginePluginManifest, PluginManifest

logger = logging.getLogger("nds.plugins")

class PluginLibsManager:
    DONE = ".install-complete"
    @classmethod
    def _is_ready(cls, target: Path) -> bool:
        return (target / cls.DONE).exists()


    @staticmethod
    def _engine_freeze() -> dict[str, str]:
        return {
            canonicalize_name(dist.metadata["Name"]): dist.version
            for dist in distributions() if dist.metadata["Name"]
        }

    @classmethod
    def fingerprint(cls, reqs: list[str], freeze: dict[str, str]) -> str:
        hash = hashlib.sha256()
        hash.update("\n".join(reqs).encode())
        hash.update("\n".join(f"{key}=={version}" for key, version in sorted(freeze.items())).encode())
        return hash.hexdigest()[:16]

    @classmethod
    def ensure_libs(cls, manifests: Union[list[PluginManifest], list[EnginePluginManifest]], libs_root: Path, allow_install: bool = True) -> Optional[Path]:
        reqs = sorted({req for manifest in manifests for req in manifest.python_dependencies})
        if not reqs:
            return None

        freeze = cls._engine_freeze()
        target = libs_root / cls.fingerprint(reqs, freeze)
        if target.exists():
            return target

        if not allow_install:
            raise PluginPythonDependencyError(
                f"Plugin libs {target.name} not installed. "
                "Libs should only be installed by the server setup."
            )
        
        libs_root.mkdir(parents=True, exist_ok=True)
        with FileLock(libs_root / ".install.lock", timeout=3600):
            # if target.exists():
            #     return target
            if cls._is_ready(target):
                return target

            shutil.rmtree(target, ignore_errors=True)
            lock_text = cls._install_into(target, reqs, freeze)
            if lock_text:
                (target / cls.DONE).write_text(lock_text)
            
            logger.info("Plugin libs ready: %s", target.name)
        
        return target
        
    @classmethod
    def _install_into(cls, tmp: Path, reqs: list[str], freeze: dict[str, str]):
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
        uv = PluginLibsManager._uv_cmd()

        logger.info("Installing plugin libraries, this may take several minutes...")
        with tempfile.TemporaryDirectory() as work_dir:
            work = Path(work_dir)
            (work / "reqs.in").write_text("\n".join(reqs))
            (work / "constraints.txt").write_text(
                "\n".join(f"{key}=={version}" for key, version in freeze.items())
            )

            res = subprocess.run(
                [*uv, "pip", "compile", str(work / "reqs.in"),
                    "-c", str(work / "constraints.txt"),
                    "--python-version", py_ver, "--only-binary=:all:",
                    "--no-header", "--no-annotate"],
                capture_output=True, text=True,
                check=True, timeout=1800
            )
            if res.returncode != 0:
                raise PluginPythonDependencyError(res.stderr)

            missing = [
                line for line in res.stdout.splitlines()
                if line.strip() and canonicalize_name(line.split("==")[0]) not in freeze
            ]

            if missing:
                subprocess.check_call(
                    [*uv, "pip", "install", "--python", sys.executable,
                        "--target", str(tmp), "--no-deps", "--only-binary=:all:", *missing],
                )
            else:
                tmp.mkdir()
            
            (tmp / "lock.txt").write_text(res.stdout)

    @staticmethod
    def _uv_cmd() -> list[str]:
        bin_dir = Path(sys.executable).parent
        for name in ("uv.exe", "uv"):
            if (bin_dir / name).exists():
                return [str(bin_dir / name)]
        
        if found := shutil.which("uv"):
            return [found]
        
        raise FileNotFoundError("uv executable not found next to the interpreter or on PATH")
