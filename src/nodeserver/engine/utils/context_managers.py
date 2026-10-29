from contextlib import contextmanager
import os
from pathlib import Path
import sys
import tempfile

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



@contextmanager
def safe_atomic_save(final_path: Path | str):
    final_path = Path(final_path)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    
    fd, temp_path = tempfile.mkstemp(dir=final_path.parent, suffix=".tmp")
    os.close(fd)
    temp_path_obj = Path(temp_path)
    
    try:
        yield temp_path_obj
        
        os.replace(temp_path_obj, final_path)
        
    except Exception as e:
        if temp_path_obj.exists():
            temp_path_obj.unlink()
        
        raise RuntimeError(f"Failed to save file atomically {e}") from e
