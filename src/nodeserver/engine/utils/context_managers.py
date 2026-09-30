from contextlib import contextmanager
from pathlib import Path
import sys


@contextmanager
def scoped_sys_path(path: Path):
    path_str = str(path.resolve())
    inserted = False
    
    print("Adding ", path_str, " to sys path")
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
        inserted = True
        
    try:
        yield
    
    finally:
        if inserted and path_str in sys.path:
            sys.path.remove(path_str)
