import os
import shutil
import stat
import sys
from pathlib import Path


def rmtree(path: Path) -> None:
    def _make_writable_and_retry(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_make_writable_and_retry)
    else:
        shutil.rmtree(path, onerror=_make_writable_and_retry)